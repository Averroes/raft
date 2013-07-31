#
# This network manager is most basic for running network requests
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

class StandardNetworkAccessManager(BaseNetworkAccessManager):
    def __init__(self, framework, cookieJar):
        BaseNetworkAccessManager.__init__(self, framework)
        self.framework = framework
        if cookieJar is not None:
            self.setCookieJar(cookieJar)
            cookieJar.setParent(None)

#        QObject.connect(self, SIGNAL('authenticationRequired(QNetworkReply, QAuthenticator)'), self.handle_authenticationRequired)
        self.proxyAuthenticationRequired.connect(self.handle_proxyAuthenticationRequired)

    def handle_proxyAuthenticationRequired(self, proxy, authenticator):
        print('proxyAuthenticationRequired', proxy, authenticator)

    def createRequest(self, operation, request, outgoingData = None):
        try: 
            url = str(request.url().toEncoded()).encode('ascii', 'ignore')
            if outgoingData is not None and type(outgoingData) == QIODevice:
                outgoingData = InterceptFormData(outgoingData)
            return StoreNetworkReply(self.framework, url, operation, request, outgoingData, self.cookieJar(),
                                     QNetworkAccessManager.createRequest(self, operation, request, outgoingData), self)
        except Exception as error:
            # exceptions will cause a segfault
            import traceback
            print('--->FIX ME:\n%s' % traceback.format_exc(error))
            request.setUrl(QUrl('about:blank'))
            return QNetworkAccessManager.createRequest(self, operation, request, outgoingData)
