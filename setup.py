#!/usr/bin/env python
#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2011 RAFT Team
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

from distutils.core import setup
import sys
import os
import glob

def walk_datalist(obj, dirname, entries):
    if '.svn' in dirname:
        return
    items = []
    for entry in entries:
        if '.svn' != entry:
            filename = os.path.join(dirname, entry)
            if os.path.isfile(filename):
                items.append(filename)
    obj[dirname] = items

def walk_MSVCP90(obj, dirname, entries):
    if obj['found']:
        return
    for entry in entries:
        if entry.lower() == 'msvcp90.dll':
            sys.path.append(dirname)
            obj['found'] = True
            return

def find_MSVCP90():
    obj = {'found': False}
    os.path.walk(os.environ.get('SystemRoot'), walk_MSVCP90, obj)
    if not obj['found']:
        os.path.walk(os.environ.get('ProgramFiles'), walk_MSVCP90, obj)

def get_datafiles():
    datalist = {}
    os.path.walk('thirdparty', walk_datalist, datalist)
    os.path.walk('data', walk_datalist, datalist)
    os.path.walk('analyzers', walk_datalist, datalist)
    data_files = []
    keys = datalist.keys()
    keys.sort()
    for key in keys:
        if len(datalist[key]) > 0:
            data_files.append((key, datalist[key]))
    return data_files

data_files = get_datafiles()
data_files.append(('extras', [os.path.join('extras', f) for f in ('RaftCapture.dtd', 'RaftCaptureProcessor.py')]))

if 'darwin' == sys.platform:
    import py2app
    setup(
        name = 'RAFT',
        app = ['raft.pyw'],
        data_files = data_files,
          options = {
            'py2app': 
            {
                'includes': ['lxml.etree', 'lxml._elementpath', 'gzip', 'sip'],
                }
            }
        )
    # need to customize qt.conf to avoid dup library loading
    fh = open('dist/RAFT.app/Contents/Resources/qt.conf', 'wb')
    fh.write('')
    fh.close()

elif 'win32' == sys.platform:
    import py2exe

    find_MSVCP90()

    setup(
        name = 'RAFT',
        console = ['raft.pyw'],
          data_files = data_files,
          options = {
            'py2exe': 
            {
                'includes': ['lxml.etree', 'lxml._elementpath', 'gzip', 'sip'],
                }
            }
          )
else:
    pass

