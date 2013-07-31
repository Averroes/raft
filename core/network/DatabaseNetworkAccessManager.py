#
# This network manager support primary interaction with RAFT db
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
from PyQt4.QtCore import QObject, SIGNAL, QUrl, QIODevice, QByteArray

from core.network.InterceptFormData import InterceptFormData
from core.network.DatabaseNetworkCache import DatabaseNetworkCache
from core.network.NetworkCacheLogger import NetworkCacheLogger
from core.network.InMemoryCache import InMemoryCache
from core.network.StoreNetworkReply import StoreNetworkReply
from core.network.CustomNetworkReply import CustomNetworkReply
from core.network.BaseNetworkAccessManager import BaseNetworkAccessManager

from core.database.constants import ResponsesTable

class DatabaseNetworkAccessManager(BaseNetworkAccessManager):

    def __init__(self, framework, cookieJar):
        BaseNetworkAccessManager.__init__(self, framework)
        self.framework = framework

        QObject.connect(self, SIGNAL('finished(QNetworkReply *)'), self.handle_finished)

        # TODO: integrate cache with DB where appropriate !
#        self.networkCache = NetworkCacheLogger(self.framework, InMemoryCache(self.framework, self), self)
        self.networkCache = InMemoryCache(self.framework, self)
        self.setCache(self.networkCache)

        if cookieJar is not None:
            self.setCookieJar(cookieJar)
            cookieJar.setParent(None)

        self.__blackholed = True
        self.__has_setNetworkAccessible = hasattr(QtNetwork.QNetworkAccessManager, 'setNetworkAccessible')

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)
        self.framework.subscribe_raft_config_updated(self.handle_raft_config_updated)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.__blackholed = self.framework.get_raft_config_value('black_hole_network', bool)

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def handle_raft_config_updated(self, name, value):
        config_name = str(name)
        if 'black_hole_network' == config_name:
            self.__blackholed = bool(value.toBool())

    def __isset_network_accessible(self):
        if self.__has_setNetworkAccessible:
            if self.__blackholed:
                self.setNetworkAccessible(self.NotAccessible)
            else:
                self.setNetworkAccessible(self.Accessible)
        return not self.__blackholed

    def createRequest(self, operation, request, outgoingData = None):
        try: 
            reply = None
            reqUrl = request.url()
            url = str(reqUrl.toEncoded()).encode('ascii', 'ignore')
            x_raft_id = self.framework.X_RAFT_ID
            if request.hasRawHeader(x_raft_id):
                raftId = str(request.rawHeader(x_raft_id))
                request.setRawHeader(x_raft_id, QByteArray())
                response = self.Data.read_responses_by_id(self.cursor, raftId)
                if response is not None:
                    reply = CustomNetworkReply(self, reqUrl, str(response[ResponsesTable.RES_HEADERS]), str(response[ResponsesTable.RES_DATA]))

            if not reply:
                if url.startswith('data:') or url.startswith('about:') or url.startswith('javascript:'):
                    reply = QtNetwork.QNetworkAccessManager.createRequest(self, operation, request, outgoingData)
                elif not self.__isset_network_accessible():
                    responses = []
                    for response in self.Data.read_responses_by_url(self.cursor, url):
                        if int(response[ResponsesTable.RES_LENGTH]) > 0 and str(response[ResponsesTable.STATUS]).startswith('2'):
                            responses.append(response)
                    if len(responses) > 0:
                        reply = CustomNetworkReply(self, reqUrl, str(responses[-1][ResponsesTable.RES_HEADERS]), str(responses[-1][ResponsesTable.RES_DATA]))
                    else:
                        # no network, but need to return reply
                        request.setUrl(QUrl('about:blank'))
                        reply = QtNetwork.QNetworkAccessManager.createRequest(self, operation, request, outgoingData)
                else:
                    if outgoingData is not None and type(outgoingData) == QIODevice:
                        outgoingData = InterceptFormData(outgoingData)
                    reply = StoreNetworkReply(self.framework, url, operation, request, outgoingData, self.cookieJar(),
                                              QtNetwork.QNetworkAccessManager.createRequest(self, operation, request, outgoingData), self)

            return reply
        except Exception, error:
            # exceptions will cause a segfault
            self.framework.report_exception(error)
            request.setUrl(QUrl('about:blank'))
            return QtNetwork.QNetworkAccessManager.createRequest(self, operation, request, outgoingData)

    def handle_finished(self, reply):
#        print('handle_finished', reply.attribute(QtNetwork.QNetworkRequest.User).toString())
        pass

