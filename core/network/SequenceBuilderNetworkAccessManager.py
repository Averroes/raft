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

from PyQt4.QtCore import QObject, SIGNAL, QUrl, QIODevice, QByteArray
from PyQt4 import QtNetwork
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest

from core.network.InterceptFormData import InterceptFormData
from core.network.StoreNetworkReply import StoreNetworkReply
from core.network.InMemoryCache import InMemoryCache
from core.network.BaseNetworkAccessManager import BaseNetworkAccessManager

class SequenceBuilderNetworkAccessManager(BaseNetworkAccessManager):
    def __init__(self, framework, cookieJar):
        BaseNetworkAccessManager.__init__(self, framework)
        self.framework = framework

        self.networkCache = InMemoryCache(self.framework, self)
        self.setCache(self.networkCache)
        if cookieJar is not None:
            self.setCookieJar(cookieJar)
            cookieJar.setParent(None)

        self.originalRequestIds = []

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

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

    def createRequest(self, operation, request, outgoingData = None):
        try: 

            originatingObject = request.originatingObject()
            if originatingObject:
                varId = originatingObject.property('RAFT_requestId')
                if varId is not None:
                    print(('createRequest', '%s->%s' % (str(varId), request.url().toEncoded().data().decode('utf-8'))))
                    request.setAttribute(QtNetwork.QNetworkRequest.User + 1, varId)
                    requestId = str(varId)
                    if requestId not in self.originalRequestIds:
                        self.originalRequestIds.append(requestId)
                        request.setAttribute(QtNetwork.QNetworkRequest.User + 2, varId)

            url = request.url().toEncoded().data().decode('utf-8')
            if outgoingData is not None and type(outgoingData) == QIODevice:
                outgoingData = InterceptFormData(outgoingData)
            return StoreNetworkReply(self.framework, url, operation, request, outgoingData, self.cookieJar(),
                                     QNetworkAccessManager.createRequest(self, operation, request, outgoingData), self)
        except Exception as error:
            # exceptions will cause a segfault
            import traceback
            print(('--->FIX ME:\n%s' % traceback.format_exc(error)))
            request.setUrl(QUrl('about:blank'))
            return QNetworkAccessManager.createRequest(self, operation, request, outgoingData)
