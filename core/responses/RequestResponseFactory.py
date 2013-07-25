#
# This factory returns RequestResponse objects as needed
#
# Authors: 
#          Gregory Fleischer (gfleischer@gmail.com)
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

from PyQt4.QtCore import QObject, QMutex

from core.database.constants import ResponsesTable
from core.responses.RequestResponse import RequestResponse
from actions import interface

import re
from urllib import parse as urlparse
import cgi

class RequestResponseFactory(QObject):

    def __init__(self, framework, parent):
        QObject.__init__(self, parent)
        self.framework = framework

        self.qlock = QMutex()
        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

        self.contentExtractor = self.framework.getContentExtractor()
        self.htmlExtractor = self.contentExtractor.getExtractor('html')
        self.jsExtractor = self.contentExtractor.getExtractor('javascript')
        self.postDataExtractor = self.contentExtractor.getExtractor('post-data')

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def fill(self, Id):
        rr = RequestResponse(self.framework)
        if not Id:
            return rr
        
        rr.responseId = Id

        self.qlock.lock()
        try:
            row = self.Data.read_responses_by_id(self.cursor, Id)
            if not row:
                return False

            responseItems = interface.data_row_to_response_items(row)

            rr.Id = Id
            rr.responseUrl = responseItems[ResponsesTable.URL]
            rr.requestHeaders = responseItems[ResponsesTable.REQ_HEADERS]
            rr.requestBody = responseItems[ResponsesTable.REQ_DATA]
            rr.responseHeaders = responseItems[ResponsesTable.RES_HEADERS]
            rr.responseBody = responseItems[ResponsesTable.RES_DATA]
            rr.responseContentType = responseItems[ResponsesTable.RES_CONTENT_TYPE]
            rr.requestHost = responseItems[ResponsesTable.REQ_HOST]
            rr.responseStatus = responseItems[ResponsesTable.STATUS]
            rr.responseHash = responseItems[ResponsesTable.RES_DATA_HASHVAL]
            rr.requestHash = responseItems[ResponsesTable.REQ_DATA_HASHVAL]
            rr.requestTime = responseItems[ResponsesTable.REQTIME]
            rr.requestDate = responseItems[ResponsesTable.REQDATE]
            rr.notes = responseItems[ResponsesTable.NOTES]
            rr.confirmed = responseItems[ResponsesTable.CONFIRMED]

            if not rr.responseContentType:
                # TODO: fix this to use better algorithm
                rr.responseContentType = 'text/html'

            rr.contentType, rr.charset = self.contentExtractor.parseContentType(rr.responseContentType)
            rr.baseType = self.contentExtractor.getBaseType(rr.contentType)

        finally:
            self.qlock.unlock()

        return rr
