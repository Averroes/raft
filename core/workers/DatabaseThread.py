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

class DatabaseThread(QThread):
    def __init__(self, framework, Data, parent = None):
        QThread.__init__(self, parent)
        self.framework = framework
        self.Data = Data
        self.qlock = QMutex()
        QObject.connect(self, SIGNAL('quit()'), self.quitHandler)
        QObject.connect(self, SIGNAL('started()'), self.startedHandler)
 
    def run(self):
        QObject.connect(self, SIGNAL('doConnectDb()'), self.connectDbHandler, Qt.DirectConnection)
        self.exec_()

    def close(self):
        self.qlock.lock()
        try:
            self.Data.close()
        finally:
            self.qlock.unlock()

    def quitHandler(self):
        self.Data.close()
        self.exit(0)

    def startedHandler(self):
        pass

    def connectDb(self, filename, callback):
        self.filename = filename
        self.callbackObj = callback
        QTimer.singleShot(50, self, SIGNAL('doConnectDb()'))

    def connectDbHandler(self):
        self.qlock.lock()
        try:
            self.Data.connect(self.filename)
        finally:
            self.qlock.unlock()

        self.callbackObj.emit(SIGNAL('connectDbFinished()'))
        
