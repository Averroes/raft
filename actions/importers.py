#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2011-2013 RAFT Team
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
# This is a module that handles the importing of various formats in to the RAFT tool
# project database format.

from lib.parsers.burpparse import burp_parse_log, burp_parse_state, burp_parse_xml, burp_parse_vuln_xml
from lib.parsers.webscarabparse import webscarab_parse_conversation
from lib.parsers.parosparse import paros_parse_message
from lib.parsers.raftparse import raft_parse_xml
from lib.parsers.appscanparse import appscan_parse_xml

def process_import(proxy_log, framework, source):
    """ Performs the importing of log in to the RAFT database """

    Data = framework.getDB()

    commit_threshold = 100

    if 'burp_state' == source:
        func = burp_parse_state
    elif 'burp_log' == source:
        func = burp_parse_log
    elif 'burp_xml' == source:
        func = burp_parse_xml
    elif 'burp_vuln_xml' == source:
        func = burp_parse_vuln_xml
    elif 'paros_message' == source:
        func = paros_parse_message
    elif 'webscarab' == source:
        func = webscarab_parse_conversation
    elif 'raft_capture_xml' == source:
        func = raft_parse_xml
    elif 'appscan_xml' == source:
        func = appscan_parse_xml
    else:
        raise Exception

    raw_cookie_list = []
    cursor = Data.allocate_thread_cursor()
    try:
        Data.set_insert_pragmas(cursor)
        count = 0
        for value in func(proxy_log):
            if 'COOKIE' == value[0]:
                if value[1]:
                    raw_cookie_list.append(str(value[1]))
                continue

            (origin, host, hostip, url, status, datetime, request, response, method, content_type, extras) = value
            if 0 == status or not request:
                pass
            else:

                if response:
                    response_headers, response_body = response[0], response[1]
                else:
                    response_headers, response_body = b'', b''

                if 'notes' in extras:
                    notes = extras['notes']
                else:
                    notes = None

                if 'confirmed' in extras:
                    try:
                        confirmed = bool(extras['confirmed'])
                    except ValueError:
                        confirmed = confirmed.lower() in ('y', '1', 'true', 'yes')
                else:
                    confirmed = None

                if 'content_length' in extras and extras['content_length']:
                    content_length = int(extras['content_length'])
                else:
                    content_length = len(response_body)

                if 'elapsed' in extras:
                    elapsed = extras['elapsed']
                else:
                    elapsed = ''

                insertlist = [None, url, request[0], request[1], response_headers, response_body,
                              status, content_length, elapsed, datetime, notes, None, confirmed, 
                              method, hostip, content_type, '%s-%s' % (source, origin), host]
                Data.insert_responses(cursor, insertlist, False)
                count += 1
                if (0 == (count % commit_threshold)):
                    Data.commit()
                    framework.signal_response_data_added()

        if not (0 == (count % commit_threshold)):
            Data.commit()
            framework.signal_response_data_added()
    except:
        Data.rollback()
        raise
    finally:
        Data.reset_pragmas(cursor)

    if len(raw_cookie_list) > 0:
        framework.import_raw_cookie_list(raw_cookie_list)
