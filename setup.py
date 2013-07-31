#!/usr/bin/env python
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

import sys
import os
from cx_Freeze import setup, Executable

# TODO: determine cleaner method for maintaining version
from raft import __version__
version = __version__

if 'win32' == sys.platform:
    if os.path.exists('setup.iss'):
        fh = open('setup.iss', 'r')
        lines = fh.read().splitlines()
        fh.close()
        for i in range(0, len(lines)):
            line = lines[i]
            if line.startswith('#define MyAppVersion'):
                lines[i] = '#define MyAppVersion "' + __version__ + '"'

        fh = open('setup.iss', 'w')
        fh.write('\n'.join(lines))
        fh.close()

includes = ['lxml.etree', 'lxml._elementpath', 'lxml.html', 'gzip', 'sip', 'PyQt4.QtWebKit', 'PyQt4.Qsci', 're']

def gather_include_files(dirname):
    files = []
    for (dirpath, dirnames, filenames) in os.walk(dirname):
        for filename in filenames:
            if filename.endswith('.py'):
                source = target = os.path.join(dirpath, filename)
                files.append((source, target))

    return files

zip_includes = []
zip_includes.extend(gather_include_files('thirdparty'))

include_files = []
include_files.extend(gather_include_files('analyzers'))
include_files.extend(('data', 'data'))
include_files.extend(gather_include_files('thirdparty'))
for f in ('RaftCapture.dtd', 'RaftCaptureProcessor.py'):
    include_files.append((os.path.join('extras', f), os.path.join('extras', f)))

bin_excludes = []

bdist_msi_options = {}

raft_ico = os.path.join('ui', os.path.join('icons', 'RAFT.ico'))
raft_icon_target = None

base = None
include_msvcr = False
if 'win32' == sys.platform:
    base = 'Win32GUI'
    targetName = 'raft.exe'
    include_msvcr = True
    raft_icon_target = raft_ico

    if '-' in version:
        version = version[0:version.find('-')] + '.0'

    # for MSI, need to add shortcut to program menu or desktop (http://stackoverflow.com/questions/15734703/use-cx-freeze-to-create-an-msi-that-adds-a-shortcut-to-the-desktop)

    # http://msdn.microsoft.com/en-us/library/windows/desktop/aa371847(v=vs.85).aspx
    shortcut_table = [
        ("DesktopShortcut",        # Shortcut
         "DesktopFolder",          # Directory_
         "RAFT",                   # Name
         "TARGETDIR",              # Component_
         "[TARGETDIR]"+targetName, # Target
         None,                     # Arguments
         None,                     # Description
         None,                     # Hotkey
         'RAFT.exe',               # Icon_
         0,                     # IconIndex
         None,                     # ShowCmd
         'TARGETDIR'               # WkDir
         )
        ]

    # Now create the table dictionary
    msi_data = {"Shortcut": shortcut_table}

    # Change some default MSI options and specify the use of the above defined tables
    bdist_msi_options = {'data': msi_data}

elif 'darwin' == sys.platform:

    # exclude dylib files from Qt
    # for example, libQsci.dylib
    # the compiled files are renamed during the build process
    # this leaves the original library name intact and cx_Freeze cannot detect this
    # so to get this to build cleanly, need to exclude libQsci.dylib file
    bin_excludes.append('libQsci.dylib')
    for f in '''QtCore
QtDeclarative
QtDesigner
QtGui
QtHelp
QtMultimedia
QtNetwork
QtOpenGL
QtScript
QtScriptTools
QtSql
QtSvg
QtTest
QtWebKit
QtXml
QtXmlPatterns'''.splitlines():
        f = f.strip()
        bin_excludes.append('lib%s.dylib' % (f))

    targetName = 'RAFT'
else: # must be linux or other platform
    targetName = 'raft.py'

exe = Executable(
    script = 'raft.py',
    base = base,
    targetName = targetName,
    icon = raft_icon_target,
    )

setup(
    name = 'RAFT',
    version = version, # TODO: determine method to expose version between setup and raft proper
    description = 'RAFT - Response Analysis and Further Testing',
    options = {
        'build_exe': {
            'includes' : includes,  
            'include_files' : include_files, 
            'zip_includes' : zip_includes, 
            'include_msvcr' : include_msvcr,
            'bin_excludes' : bin_excludes,
            } ,
        'bdist_msi': bdist_msi_options,
        },
    executables = [exe]
    )
