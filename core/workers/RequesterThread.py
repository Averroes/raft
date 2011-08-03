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

class RequesterThread(QThread):
    def __init__(self, framework, parent = None):
        QThread.__init__(self, parent)
        self.framework = framework
        self.qtimer = QTimer()
        self.qlock = QMutex()
        QObject.connect(self, SIGNAL('quit()'), self.quitHandler)
        QObject.connect(self, SIGNAL('started()'), self.startedHandler)

        self.Data = None
        self.cursor = None

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def run(self):
        QObject.connect(self, SIGNAL('queueRequest(QString, QString, QString, QString, QString)'), self.do_queueRequest, Qt.DirectConnection)
        self.exec_()

    def quitHandler(self):
        self.framework.debug_log('RequesterThread quit...')
        self.close_cursor()
        self.exit(0)

    def startedHandler(self):
        self.framework.debug_log('RequesterThread started...')
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def do_queueRequest(self, method, url, headers, body, context):
        pass


