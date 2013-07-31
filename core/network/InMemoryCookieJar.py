#
# In memory cookie jar implementation
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

from PyQt4.QtNetwork import QNetworkCookieJar
from PyQt4.QtCore import QObject, SIGNAL

class InMemoryCookieJar(QNetworkCookieJar):
    def __init__(self, framework, parent = None):
        QNetworkCookieJar.__init__(self, parent)
        self.framework = framework
        self.__read_only = False

    def cookiesForUrl(self, url):
        return QNetworkCookieJar.cookiesForUrl(self, url)

    def setCookiesFromUrl(self, cookieList, url):
        if self.__read_only:
            return True
        resp = QNetworkCookieJar.setCookiesFromUrl(self, cookieList, url)
        if resp:
            self.emit(SIGNAL('cookieJarUpdated()'))
        return resp

    def allCookies(self):
        return QNetworkCookieJar.allCookies(self)

    def setAllCookies(self, cookieList):
        if not self.__read_only:
            QNetworkCookieJar.setAllCookies(self, cookieList)
            self.emit(SIGNAL('cookieJarUpdated()'))

    def clear_cookies(self):
        self.setAllCookies([])

    def subscribe_cookie_jar_updated(self, callback):
        QObject.connect(self, SIGNAL('cookieJarUpdated()'), callback, Qt.DirectConnection)

    def set_read_only(self, read_only):
        self.__read_only = read_only
        # TODO: fix this!
        self.__read_only = False
