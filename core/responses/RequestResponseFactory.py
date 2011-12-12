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
from utility import ContentHelper

import re
from urllib2 import urlparse
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
        rr = RequestResponse()
        if not Id:
            return rr
        
        rr.responseId = Id

        self.qlock.lock()
        try:
            row = self.Data.read_responses_by_id(self.cursor, Id)
            if not row:
                return False
            responseItems = [m or '' for m in list(row)]
            rr.Id = Id
            rr.responseUrl = str(responseItems[ResponsesTable.URL])
            rr.requestHeaders = str(responseItems[ResponsesTable.REQ_HEADERS])
            rr.requestBody = str(responseItems[ResponsesTable.REQ_DATA])
            rr.responseHeaders = str(responseItems[ResponsesTable.RES_HEADERS])
            rr.responseBody = str(responseItems[ResponsesTable.RES_DATA])
            rr.responseContentType = str(responseItems[ResponsesTable.RES_CONTENT_TYPE])
            rr.requestHost = str(responseItems[ResponsesTable.REQ_HOST])
            rr.responseStatus = str(responseItems[ResponsesTable.STATUS])
            rr.responseHash = str(responseItems[ResponsesTable.RES_DATA_HASHVAL])
            rr.requestHash = str(responseItems[ResponsesTable.REQ_DATA_HASHVAL])
            rr.requestTime = str(responseItems[ResponsesTable.REQTIME])
            rr.requestDate = str(responseItems[ResponsesTable.REQDATE])
            rr.notes = str(responseItems[ResponsesTable.NOTES])
            rr.confirmed = str(responseItems[ResponsesTable.CONFIRMED])
            rr.requestParams = {}

            # extract request parameters
            # TODO: repeated parameters clobber earlier values
            splitted = urlparse.urlsplit(rr.responseUrl)
            if splitted.query:
                qs_values = urlparse.parse_qs(splitted.query, True)
                for name, value in qs_values.iteritems():
                    rr.requestParams[name] = value
            postDataResults = self.postDataExtractor.process_request(rr.requestHeaders, rr.requestBody)
            for name, value in postDataResults.name_values_dictionary.iteritems():
                rr.requestParams[name] = value

            if not rr.responseContentType:
                # TODO: fix this to use better algorithm
                rr.responseContentType = 'text/html'

            rr.contentType, rr.charset = self.contentExtractor.parseContentType(rr.responseContentType)

            # TODO: not really ASCII
            rr.requestASCIIHeaders, rr.requestASCIIBody, rr.rawRequest = ContentHelper.combineRaw(rr.requestHeaders, rr.requestBody)
            rr.responseASCIIHeaders, rr.responseASCIIBody, rr.rawResponse = ContentHelper.combineRaw(rr.responseHeaders, rr.responseBody, rr.charset)

            rr.baseType = self.contentExtractor.getBaseType(rr.contentType)
            if 'html' == rr.baseType:
                rr.results = self.htmlExtractor.process(rr.responseBody, rr.responseUrl, rr.charset, None)
            elif 'javascript' == rr.baseType:
                rr.results = self.jsExtractor.process(rr.responseASCIIBody, rr.responseUrl, rr.charset, None)
            else:
                # TODO: implement more types
                pass


        finally:
            self.qlock.unlock()

        return rr
