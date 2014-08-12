#
# Class that exposes the command line functionality
#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2013 RAFT Team
#
# This file is part of RAFT.
#
# RAFT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# RAFT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RAFT.  If not, see <http://www.gnu.org/licenses/>.
#
import sys
import argparse
import os
import bz2
import lzma
import glob

from core.database import database
from core.data.RaftDbCapture import RaftDbCapture

from utility.ScriptLoader import ScriptLoader

from lib.parsers.burpparse import burp_parse_log, burp_parse_state, burp_parse_xml, burp_parse_vuln_xml
from lib.parsers.webscarabparse import webscarab_parse_conversation
from lib.parsers.parosparse import paros_parse_message
from lib.parsers.raftparse import raft_parse_xml, ParseAdapter
from lib.parsers.appscanparse import appscan_parse_xml

from raft import __version__

class RaftCmdLine():
    # TODO: refactor this definition to be shared with importers
    FILE_PROCESSOR_DEFINTIONS = {
        'raft_capture_xml' : raft_parse_xml,
        'burp_log' : burp_parse_log,
        'burp_xml' : burp_parse_xml,
        'burp_vuln_xml' : burp_parse_vuln_xml,
        'burp_state' : burp_parse_state,
        'appscan_xml' : appscan_parse_xml,
        'webscarab' : webscarab_parse_conversation,
        'paros_message' : paros_parse_message,
        }
    def __init__(self):
        self.scripts = {}
        self.scriptLoader = ScriptLoader()
        self.Data = None

    def cleanup(self):
        if self.Data:
            self.Data.close()

    def process_args(self, args):

        do_create = getattr(args, 'create')
        do_import = getattr(args, 'import')
        do_export = getattr(args, 'export')
        do_parse = getattr(args, 'parse')

        # was DB file specified?
        db_filename = getattr(args, 'db')
        if db_filename is not None:
            if not db_filename.endswith('.raftdb'):
                db_filename += '.raftdb'

            if not os.path.exists(db_filename):
                if not do_create:
                    sys.stderr.write('\nDB file [%s] does not exist\n' % (db_filename))
                    return 1
                else:
                    sys.stderr.write('\nWill create database: %s\n' %(db_filename))

            self.Data = database.Db(__version__, self.report_exception)
            self.Data.connect(db_filename)
            sys.stderr.write('\nAttaching database: %s\n' %(db_filename))
        else:
            if do_export or do_import:
                sys.stderr.write('\nDB file is required\n' % (db_filename))
                return 1

        # setup any capture filters
        self.capture_filter_scripts = []
        arg = getattr(args, 'capture_filter')
        if arg is not None:
            for filearg in arg:
                self.capture_filter_scripts.append(self.load_script_file(filearg))

        # setup any capture filters
        self.process_capture_scripts = []
        arg = getattr(args, 'process_capture')
        if arg is not None:
            for filearg in arg:
                self.process_capture_scripts.append(self.load_script_file(filearg))

        if do_export:
            filename = getattr(args, 'output_file')
            if filename.endswith('.xml.xz'):
                fh = lzma.LZMAFile(filename, 'w')
            elif filename.endswith('.xml.bz2'):
                fh = bz2.BZ2File(filename, 'w')
            elif filename.endswith('.xml'):
                fh = open(filename, 'wb')
            else:
                sys.stderr.write('\nUnsupported output file type [%s]\n' % (filename))
                return 1
            self.export_to_raft_capture(filename, fh)
        elif do_import:
            self.run_process_loop(args, self.import_one_file)
        elif do_parse:
            self.run_process_loop(args, self.parse_one_file)
        else:
            sys.stderr.write('\nNo recognized options\n')

        return 0

    def report_exception(self, error):
        print(error)

    def setup_script_initializers(self):
        for key, script_env in self.scripts.items():
            initializer = script_env.functions.get('initialize')
            if initializer and not script_env['initialized']:
                initializer()
                script_env['initialized'] = True

    def reset_script_begin_end(self):
        for key, script_env in self.scripts.items():
            script_env['begin_called'] = False
            script_env['end_called'] = False

    def call_script_method_with_filename(self, script_env, method, filename):
        method_func = script_env.functions.get(method)
        if method_func and not script_env[method + '_called']:
            method_func(filename)
            script_env[method + '_called'] = True

    def run_process_loop(self, args, call_func):
        self.setup_script_initializers()
        for name, func in self.FILE_PROCESSOR_DEFINTIONS.items():
            arg = getattr(args, name)
            if arg is None:
                continue
            for filearg in arg:
                if '*' in filearg:
                    file_list = glob.glob(filearg)
                elif os.path.exists(filearg):
                    file_list = [filearg]
                for filename in file_list:
                    call_func(filename, func, name)

    def export_to_raft_capture(self, filename, fhandle):
        """ Export to RAFT capture format """
        sys.stderr.write('\nExporting to [%s]\n' % (filename))
        self.reset_script_begin_end()
        self.setup_script_initializers()
        filters = []
        for script_env in self.capture_filter_scripts:
            self.call_script_method_with_filename(script_env, 'begin', filename)
            capture_filter = script_env.functions.get('capture_filter')
            if capture_filter:
                filters.append(capture_filter)

        adapter = ParseAdapter()
        count = 0
        Data = self.Data
        cursor = Data.allocate_thread_cursor()
        try:
            fhandle.write(b'<raft version="1.0">\n')
            for row in Data.read_all_responses(cursor):
                capture = RaftDbCapture()
                capture.populate_by_dbrow(row)

                skip = False
                for capture_filter in filters:
                    result = capture_filter(capture)
                    if not result:
                        skip = True
                        break

                if not skip:
                    fhandle.write(adapter.format_as_xml(capture).encode('utf-8'))
                    count += 1

            fhandle.write(b'</raft>')
            fhandle.close()

            sys.stderr.write('\nExported [%d] records\n' % (count))

        finally:
            cursor.close()
            Data.release_thread_cursor(cursor)
            Data, cursor = None, None

        for script_env in self.capture_filter_scripts:
            self.call_script_method_with_filename(script_env, 'end', filename)

    def import_one_file(self, filename, func, funcname):
        """ Import one file using specified parser function"""
        adapter = ParseAdapter()
        sys.stderr.write('\nImporting [%s]\n' % (filename))
        self.reset_script_begin_end()
        filters = []
        for script_env in self.capture_filter_scripts:
            self.call_script_method_with_filename(script_env, 'begin', filename)
            capture_filter = script_env.functions.get('capture_filter')
            if capture_filter:
                filters.append(capture_filter)

        count = 0
        commit_threshold = 100
        Data = self.Data
        cursor = Data.allocate_thread_cursor()
        try:
            Data.set_insert_pragmas(cursor)
            for result in func(filename):
                capture = adapter.adapt(result)
                skip = False
                for capture_filter in filters:
                    result = capture_filter(capture)
                    if not result:
                        skip = True
                        break
                if not skip:
                    insertlist = [None, capture.url, capture.request_headers, capture.request_body, capture.response_headers, capture.response_body,
                                  capture.status, capture.content_length, capture.elapsed, capture.datetime, capture.notes, None, capture.confirmed, 
                                  capture.method, capture.hostip, capture.content_type, '%s-%s' % (funcname, capture.origin), capture.host]
                    Data.insert_responses(cursor, insertlist, False)
                    count += 1
                    if (0 == (count % commit_threshold)):
                        Data.commit()

            if not (0 == (count % commit_threshold)):
                Data.commit()

            sys.stderr.write('\nInserted [%d] records\n' % (count))

        except Exception as error:
            Data.rollback()
            print(error)
            # TODO: should continue(?)
            raise error
        finally:
            Data.reset_pragmas(cursor)
            cursor.close()
            Data.release_thread_cursor(cursor)
            Data, cursor = None, None

        for script_env in self.capture_filter_scripts:
            self.call_script_method_with_filename(script_env, 'end', filename)

    def parse_one_file(self, filename, func, funcname):
        """ Parse one file using specified parser function"""
        adapter = ParseAdapter()
        sys.stderr.write('\nProcessing [%s]\n' % (filename))
        self.reset_script_begin_end()
        filters = []
        processors = []
        for script_env in self.capture_filter_scripts:
            self.call_script_method_with_filename(script_env, 'begin', filename)
            capture_filter = script_env.functions.get('capture_filter')
            if capture_filter:
                filters.append(capture_filter)
        for script_env in self.process_capture_scripts:
            self.call_script_method_with_filename(script_env, 'begin', filename)
            process_capture = script_env.functions.get('process_capture')
            if process_capture:
                processors.append(process_capture)
        try:
            for result in func(filename):
                capture = adapter.adapt(result)
                skip = False
                for capture_filter in filters:
                    result = capture_filter(capture)
                    if not result:
                        skip = True
                        break
                if not skip:
                    for processor in processors:
                        result = processor(capture)

        except Exception as error:
            print(error)
            # TODO: should continue(?)
            raise error

        for script_env in self.capture_filter_scripts:
            self.call_script_method_with_filename(script_env, 'end', filename)
        for script_env in self.process_capture_scripts:
            self.call_script_method_with_filename(script_env, 'end', filename)

    def load_script_file(self, filename):
        if filename in self.scripts:
            return self.scripts[filename]
        script_env = self.scriptLoader.load_from_file(filename)
        script_env['initialized'] = False
        self.scripts[filename] = script_env
        return script_env

def main():
    sys.stderr.write('\nRaftCmdLine - version: %s\n' %  (__version__))

    parser = argparse.ArgumentParser(description='Run RAFT processing from command line')
    parser.add_argument('--db', nargs='?', help='Specify a RAFT database file')
    parser.add_argument('--create', action='store_const', const=True, default=False, help='Create the database (if needed)')
    parser.add_argument('--import', action='store_const', const=True, default=False, help='Import list of files into database')
    parser.add_argument('--export', action='store_const', const=True, default=False, help='Export the RAFT database into a RAFT XML capture file')
    parser.add_argument('--parse', action='store_const', const=True, default=False, help='Parse list of files and run processing')
    parser.add_argument('--output-file', nargs='?', help='Output file to write results into')
    parser.add_argument('--capture-filter', nargs='*', help='A Python file with a function or single class containing: "capture_filter"')
    parser.add_argument('--process-capture', nargs='*', help='A Python file with a function or single class containing: "process_capture"')
    parser.add_argument('--raft-capture-xml', nargs='*', help='A list of RAFT xml captgure files')
    parser.add_argument('--burp-log', nargs='*', help='A list of Burp log files')
    parser.add_argument('--burp-xml', nargs='*', help='A list of Burp XML files')
    parser.add_argument('--burp-vuln-xml', nargs='*', help='A list of Burp vulnerability report in XML format')
    parser.add_argument('--burp-state', nargs='*', help='A list of Burp saved state files')
    parser.add_argument('--appscan-xml', nargs='*', help='A list of AppScan XML report files')
    parser.add_argument('--webscarab', nargs='*', help='A list of WebScarab locations')
    parser.add_argument('--paros-message', nargs='*', help='A list of Paros message files')

    args = parser.parse_args()

    raftCmdLine = RaftCmdLine()
    rc = -1
    try:
        rc = raftCmdLine.process_args(args)
    finally:
        raftCmdLine.cleanup()

    sys.exit(rc)

if '__main__' == __name__:
    main()
