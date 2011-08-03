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
from PyQt4.QtCore import Qt, QObject, SIGNAL, QThread, QTimer, QMutex

import traceback

class ImporterThread(QThread):
    def __init__(self, framework, parent = None):
        QThread.__init__(self, parent)
        self.framework = framework
        self.qlock = QMutex()
        self.cursor = None
        QObject.connect(self, SIGNAL('quit()'), self.quitHandler)
        QObject.connect(self, SIGNAL('started()'), self.startedHandler)

    def run(self):
        QObject.connect(self, SIGNAL('do_runImport()'), self.handle_runImport, Qt.DirectConnection)
        self.exec_()

    def quitHandler(self):
        if self.cursor:
            self.cursor.close()
        self.exit(0)

    def startedHandler(self):
        pass

    def runImport(self, importers, proxy_file, source, callback):
        self.importers = importers
        self.proxy_file = proxy_file
        self.source = source
        self.callbackObj = callback
        QTimer.singleShot(50, self, SIGNAL('do_runImport()'))

    def runImportList(self, importers, proxy_filelist, source, callback):
        self.importers = importers
        self.proxy_file = None
        self.proxy_filelist = proxy_filelist
        self.source = source
        self.callbackObj = callback
        QTimer.singleShot(50, self, SIGNAL('do_runImport()'))

    def handle_runImport(self):
        if self.qlock.tryLock():
            try:
                if self.proxy_file:
                    self.importers.process_import(self.proxy_file, self.framework, self.source)
                else:
                    for proxy_file in self.proxy_filelist:
                        self.importers.process_import(str(proxy_file), self.framework, self.source)
            finally:
                self.qlock.unlock()
        
        self.callbackObj.emit(SIGNAL('runImportFinished()'))
