#
# This network manager is isolated for sequence building
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

from PyQt4 import QtNetwork
from PyQt4.QtNetwork import QNetworkAccessManager

from PyQt4.QtCore import QObject, SIGNAL, QUrl

from core.network.BaseNetworkAccessManager import BaseNetworkAccessManager
from core.network.InMemoryCache import InMemoryCache
from core.network.CustomNetworkReply import CustomNetworkReply

from core.database.constants import ResponsesTable
from actions import interface

class OfflineNetworkAccessManager(BaseNetworkAccessManager):
    def __init__(self, framework, cookieJar):
        BaseNetworkAccessManager.__init__(self, framework)
        self.framework = framework

        self.networkCache = InMemoryCache(self.framework, self)
        self.setCache(self.networkCache)
        if cookieJar is not None:
            self.setCookieJar(cookieJar)
            cookieJar.setParent(None)

        self.request_lookaside = {}
        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.request_lookaside = {}

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def createRequest(self, operation, request, outgoingData = None):
        reply = None
        try: 
            requestUrl = request.url()
            scheme = str(requestUrl.scheme())
            if scheme in ('data', 'about', 'javascript'):
                reply = QNetworkAccessManager.createRequest(self, operation, request, outgoingData)
            elif scheme in ('http', 'https'):
                url = requestUrl.toEncoded().data().decode('utf-8')
                url_response = None
                if url in self.request_lookaside:
                    url_response = self.request_lookaside[url]
                else:
                    responses = []
                    for row in self.Data.read_responses_by_url(self.cursor, url):
                        responseItems = interface.data_row_to_response_items(row)
                        response_length = str(responseItems[ResponsesTable.RES_LENGTH])
                        if response_length and int(response_length) > 0 and str(responseItems[ResponsesTable.STATUS]).startswith('2'):
                            responses.append(responseItems)
                        if len(responses) > 0:
                            url_response = responses[-1]
                            # TODO: implement max size limit
                            self.request_lookaside[url] = url_response
                    if not url_response:
                        # try again, with base url
                        if '?' in url:
                            base_url = url[0:url.index('?')]
                        else:
                            base_url = url
                        for row in self.Data.read_responses_starting_with_url(self.cursor, base_url):
                            responseItems = interface.data_row_to_response_items(row)
                            response_length = str(responseItems[ResponsesTable.RES_LENGTH])
                            if response_length and int(response_length) > 0 and str(responseItems[ResponsesTable.STATUS]).startswith('2'):
                                responses.append(responseItems)
                            if len(responses) > 0:
                                url_response = responses[-1]
                                self.request_lookaside[url] = url_response
                if url_response:
                    reply = CustomNetworkReply(self, requestUrl, url_response[ResponsesTable.RES_HEADERS], url_response[ResponsesTable.RES_DATA])

        except Exception as error:
            self.framework.report_implementation_error(error)

        if not reply:
            # must always return reply
            request.setUrl(QUrl('about:blank'))
            reply = QNetworkAccessManager.createRequest(self, operation, request, outgoingData)

        return reply
