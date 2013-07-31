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

import re

from PyQt4.QtCore import Qt, QObject, SIGNAL, QThread, QTimer, QMutex
from PyQt4.QtGui import QTreeWidgetItem

from core.database.constants import ResponsesTable
from actions import interface

class SearchThread(QThread):
    def __init__(self, framework, treeViewModel):
        QThread.__init__(self)
        self.framework = framework
        self.treeViewModel = treeViewModel
        self.qlock = QMutex()
        self.cursor = None
        QObject.connect(self, SIGNAL('finished()'), self.quitHandler)
        QObject.connect(self, SIGNAL('started()'), self.startedHandler)

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)
        self.canceled = False

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
        QObject.connect(self, SIGNAL('performSearch()'), self.performSearchHandler, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('cancelSearch()'), self.cancelSearchHandler, Qt.DirectConnection)
        self.exec_()

    def quitHandler(self):
        self.close_cursor()
        self.exit(0)

    def startedHandler(self):
        pass

    def startSearch(self, searchCriteria, callback):
        self.searchCriteria = searchCriteria
        self.callbackObj = callback
        self.canceled = False
        QTimer.singleShot(50, self, SIGNAL('performSearch()'))

    def stopSearch(self):
        QTimer.singleShot(50, self, SIGNAL('cancelSearch()'))

    def cancelSearchHandler(self):
        # TODO: consider a real threading primitive
        self.canceled = True 

    def performSearchHandler(self):
        text = self.searchCriteria.text
        options = self.searchCriteria.options
        locations = self.searchCriteria.locations

        self.reqheaders = locations['RequestHeaders']
        self.reqbody = locations['RequestBody']
        self.resheaders = locations['ResponseHeaders']
        self.resbody = locations['ResponseBody']
        self.requrl = locations['RequestUrl']
        self.notes = locations['AnalystNotes']

        caseSensitive = options['CaseSensitive']
        invertSearch = options['InvertSearch']

        re_search, re_search_bytes = None, None
        if options['Wildcard']:
            wildcardSearch = re.escape(text).replace('\*','.*').replace('\?','.?')
            wildcardSearch_bytes = re.escape(text.encode('utf-8')).replace(b'\*',b'.*').replace(b'\?',b'.?')
            if caseSensitive:
                re_search = re.compile(wildcardSearch)
                re_search_bytes = re.compile(wildcardSearch_bytes)
            else:
                re_search = re.compile(wildcardSearch, re.I)
                re_search_bytes = re.compile(wildcardSearch_bytes, re.I)
        elif options['RegularExpression']:
            if caseSensitive:
                re_search = re.compile(text)
                re_search_bytes = re.compile(text.encode('utf-8'))
            else:
                re_search = re.compile(text, re.I)
                re_search_bytes = re.compile(text.encode('utf-8'), re.I)

        if re_search:
            self.str_strategy = lambda v: re_search.search(v)
            self.bytes_strategy = lambda v: re_search_bytes.search(v)
        else:
            if caseSensitive:
                self.str_strategy = lambda v: -1 != v.find(text)
                self.bytes_strategy = lambda v: -1 != v.find(text.encode('utf-8'))
            else:
                ltext = text.lower()
                self.str_strategy = lambda v: -1 != v.lower().find(ltext)
                self.bytes_strategy = lambda v: -1 != v.lower().find(ltext.encode('utf-8'))

        for row in self.Data.execute_search(self.cursor, self.reqbody or self.resbody):
            if self.canceled:
                break
            responseItems = interface.data_row_to_response_items(row)
            if self.isMatch(responseItems):
                if not invertSearch:
                    self.fill(responseItems)
            elif invertSearch:
                self.fill(responseItems)

        self.callbackObj.emit(SIGNAL('searchFinished()'))

    def isMatch(self, responseItems):
        # TODO: work on lines
        if self.reqheaders:
            if self.bytes_strategy(responseItems[ResponsesTable.REQ_HEADERS]):
                return True
        if self.reqbody:
            if self.bytes_strategy(responseItems[ResponsesTable.REQ_DATA]):
                return True
        if self.resheaders:
            if self.bytes_strategy(responseItems[ResponsesTable.RES_HEADERS]):
                return True
        if self.resbody:
            if self.bytes_strategy(responseItems[ResponsesTable.RES_DATA]):
                return True
        if self.requrl:
            if self.str_strategy(responseItems[ResponsesTable.URL]):
                return True
        if self.notes:
            if self.str_strategy(responseItems[ResponsesTable.NOTES]):
                return True

    def fill(self, responseItems):
        self.treeViewModel.append_data([responseItems])
