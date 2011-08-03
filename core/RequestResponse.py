#
# This module supports the parsing and objectification of the HTTP Request/Response
#
# Author: Seth Law (seth.w.law@gmail.com)
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

import PyQt4

from PyQt4 import Qsci

from utility import ContentHelper
from core.database.constants import ResponsesTable

from cStringIO import StringIO

class RequestResponse(object):
    
    contentTypeMapping = {
            # TODO: complete
            'json' : 'javascript',
            'javascript': 'javascript',
            'html' : 'html',
            'text/xml' : 'xml',
            'text/html' : 'html',
            'text/xhtml' : 'html',
            'text/css' : 'css',
            'text/plain' : 'text',
            }
    
    lexerMapping = {
            'text' : None,
            'javascript' : Qsci.QsciLexerJavaScript,
            'html' : Qsci.QsciLexerHTML,
            'xml' : Qsci.QsciLexerXML,
            'css' : Qsci.QsciLexerCSS,
            }
    
    requestHeaders = ''
    requestBody = ''
    requestHost = ''
    requestHash = ''
    requestDate = ''
    requestTime = ''
    rawRequest = ''
    responseHeaders = ''
    responseBody=''
    responseStatus = ''
    responseHash = ''
    responseContentType = ''
    rawResponse = ''
    notes = ''
    confirmed = ''
    
    comments = []
    scripts = []
    links = []
    forms = []
    inputs = []
    
    
    def __init__(self,framework,Id):
        if not Id:
            return None
        self.framework = framework
                
        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)
        
        self.contentExtractor = self.framework.getContentExtractor()
        self.htmlExtractor = self.contentExtractor.getExtractor('html')
        
        self.fill(Id)
        
        
    def fill(self,Id):
        if not Id:
            return
        
        self.responseId = Id
        
        #print "Looking for ID # %d" % Id

        row = self.Data.read_responses_by_id(self.cursor, Id)
        if not row:
            return

        responseItems = [m or '' for m in list(row)]

        self.responseUrl = str(responseItems[ResponsesTable.URL])

        self.requestHeaders = str(responseItems[ResponsesTable.REQ_HEADERS])
        self.requestBody = str(responseItems[ResponsesTable.REQ_DATA])
        self.responseHeaders = str(responseItems[ResponsesTable.RES_HEADERS])
        self.responseBody = str(responseItems[ResponsesTable.RES_DATA])
        self.responseContentType = str(responseItems[ResponsesTable.RES_CONTENT_TYPE])
        self.requestHost = str(responseItems[ResponsesTable.REQ_HOST])
        self.responseStatus = str(responseItems[ResponsesTable.STATUS])
        self.responseHash = str(responseItems[ResponsesTable.RES_DATA_HASHVAL])
        self.requestHash = str(responseItems[ResponsesTable.REQ_DATA_HASHVAL])
        self.requestTime = str(responseItems[ResponsesTable.REQTIME])
        self.requestDate = str(responseItems[ResponsesTable.REQDATE])
        self.notes = str(responseItems[ResponsesTable.NOTES])
        self.confirmed = str(responseItems[ResponsesTable.CONFIRMED])

        if not self.responseContentType:
            # TODO: fix this to use better algorithm
            self.responseContentType = 'text/html'
        self.charset = ContentHelper.getCharSet(self.responseContentType)
        self.notes = str(responseItems[ResponsesTable.NOTES])
        self.confirmed = str(responseItems[ResponsesTable.CONFIRMED])

        self.requestASCIIHeaders, self.requestASCIIBody, self.rawRequest = ContentHelper.combineRaw(self.requestHeaders, self.requestBody)
        self.responseASCIIHeaders, self.responseASCIIBody, self.rawResponse = ContentHelper.combineRaw(self.responseHeaders, self.responseBody, self.charset)
        
        if 'html' in self.responseContentType:
            results = None
            results = self.htmlExtractor.process(self.responseBody, self.responseUrl, self.charset, results)
            self.comments = results.comments
            self.scripts = results.all_scripts
            self.links = results.links
            self.forms = results.forms
            self.inputs = results.other_inputs

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
