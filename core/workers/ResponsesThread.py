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
from PyQt4.QtGui import *

import traceback

from core.database.constants import ResponsesTable

class ResponsesThread(QThread):
    def __init__(self, framework, treeViewModel, parent = None):
        QThread.__init__(self, parent)
        self.framework = framework
        self.treeViewModel = treeViewModel
        self.qlock = QMutex()
        self.cursor = None
        self.lastId = -1
        self.fillAll = False
        self.doCallback = False
        self.callbackObj = None
        QObject.connect(self, SIGNAL('quit()'), self.quitHandler)
        QObject.connect(self, SIGNAL('started()'), self.startedHandler)

        self.Data = None
        self.cursor = None

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.fillResponses(True)

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None
 
    def run(self):
        QObject.connect(self, SIGNAL('doFillResponses()'), self.fillResponsesHandler, Qt.DirectConnection)
        self.exec_()

    def quitHandler(self):
        self.framework.debug_log('ResponsesThread quit...')
        if self.cursor:
            self.cursor.close()
        self.exit(0)

    def startedHandler(self):
        self.framework.debug_log('ResponsesThread started...')
        self.framework.subscribe_response_data_added(self.fillResponsesHandler)
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def fillResponses(self, fillAll, callback = None):
        self.fillAll = fillAll
        if callback:
            self.doCallback = True
            self.callbackObj = callback
        else:
            self.doCallback = False
        QTimer.singleShot(50, self, SIGNAL('doFillResponses()'))

    def fillResponsesHandler(self, fillAll = False):
        if self.qlock.tryLock():
            try:

                if self.fillAll:
                    self.fillAll = False
                    self.treeViewModel.clearModel()
                    self.lastId = -1

                rows = self.Data.read_newer_responses_info(self.cursor, self.lastId)
                    
                count = 0
                datarows = []
                for row in rows:
                    count += 1
                    if 0 == (count % 100):
                        self.treeViewModel.append_data(datarows)
                        datarows = []
                        self.yieldCurrentThread()

                    responseItems = [m or '' for m in list(row)]

                    Id = str(row[ResponsesTable.ID])
                    self.lastId = int(Id)

                    if str(responseItems[ResponsesTable.CONFIRMED]).lower() in ('y', '1'):
                        confirmed = "Yes"
                    else:
                        confirmed = ""

                    responseItems[ResponsesTable.CONFIRMED]  = confirmed
                    datarows.append(responseItems)
                    
                self.treeViewModel.append_data(datarows)

            except Exception as error:
                print(('FIX ME! ERROR: %s' % (traceback.format_exc(error))))
            finally:
                self.qlock.unlock()

        if self.doCallback:
            self.doCallback = False
            self.callbackObj.emit(SIGNAL('fillResponsesFinished()'))
        
