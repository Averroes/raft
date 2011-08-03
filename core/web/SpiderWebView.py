#
# Implements webview for spidering
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

import PyQt4

from PyQt4 import QtWebKit, QtNetwork
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from core.web.SpiderWebPage import SpiderWebPage
from core.network.SpiderNetworkAccessManager import SpiderNetworkAccessManager

class SpiderWebView(QtWebKit.QWebView):
    def __init__(self, framework, pageController, cookieJar, parent = None):
        QtWebKit.QWebView.__init__(self, parent)
        self.framework = framework
        self.pageController = pageController

        self.qlock = QMutex()

        self.__networkAccessManager = SpiderNetworkAccessManager(self.framework, cookieJar)
        QObject.connect(self.__networkAccessManager, SIGNAL('finished(QNetworkReply *)'), self.process_request_finished)
        self.__page = self.__new_page()
        self.setPage(self.__page)
        self.__created_windows = []

    def __new_page(self):
        page = SpiderWebPage(self.framework, self.pageController, self) # TODO: or parent?
        page.setNetworkAccessManager(self.__networkAccessManager)
        return page

    def process_request_finished(self, reply):
        self.qlock.lock()
        try:
            varId = reply.attribute(QtNetwork.QNetworkRequest.User)
            if varId.isValid():
                responseId = str(varId.toString())
                print('got response --> %s' % (responseId))
                self.pageController.append_response(responseId)
        finally:
            self.qlock.unlock()

    def cleanup(self):
        self.qlock.lock()
        try:
            self.pageController.clear_windows()
        finally:
            self.qlock.unlock()

    def createWindow(self, windowType):
        self.qlock.lock()
        try:
            print('***** creating window')
            return self.pageController.add_window()
        finally:
            self.qlock.unlock()


