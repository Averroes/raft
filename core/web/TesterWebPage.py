#
# Implements a standard web page that has user interaction
#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2011-2013 RAFT Team
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

from core.web.BaseWebPage import BaseWebPage

class TesterWebPage(BaseWebPage):
    def __init__(self, framework, interactor, parent = None):
        BaseWebPage.__init__(self, framework, parent)
        self.framework = framework
        self.loadFinished.connect(self.handle_loadFinished)
        self.contentsChanged.connect(self.handle_contentsChanged)
        self.unsupportedContent.connect(self.handle_unsupportedContent)
        self.interactor = interactor
        self.setForwardUnsupportedContent(True)

    def set_javascript_enabled(self, javascript_enabled):
        settings = self.settings()
        settings.setAttribute(QtWebKit.QWebSettings.JavascriptEnabled, javascript_enabled)

    def set_page_settings(self, settings):
        # common settings handled by base
        settings.setAttribute(QtWebKit.QWebSettings.JavascriptCanOpenWindows, False)
            
    def javaScriptConsoleMessage(self, message, lineNumber, sourceID):
        self.interactor.log('javaScriptConsoleMessage', (lineNumber, sourceID, message))

    def userAgentForUrl(self, url):
        return self.framework.useragent()

    def handle_loadFinished(self, ok):
        self.mainFrame().addToJavaScriptWindowObject("__RAFT__", self)

    def handle_contentsChanged(self):
        pass

    def javaScriptConfirm(self, frame, msg):
        return self.interactor.confirm(frame, msg)

    def acceptNavigationRequest(self, frame, request, navigationType):
        return True

    def handle_unsupportedContent(self, reply):
        # TODO: implement
        pass
