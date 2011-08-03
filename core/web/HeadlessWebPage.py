#
# Implements a web page that has no user interaction
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

from PyQt4 import QtWebKit
from PyQt4.QtCore import *

from core.web.BaseWebPage import BaseWebPage

class HeadlessWebPage(BaseWebPage):
    def __init__(self, framework, callbackLogger, parent = None):
        BaseWebPage.__init__(self, framework, parent)
        self.framework = framework
        self.callbackLogger = callbackLogger

    def set_page_settings(self, settings):
        # common settings handled by base
        settings.setAttribute(QtWebKit.QWebSettings.JavascriptCanOpenWindows, False)

    @PyQt4.QtCore.pyqtSlot(name='shouldInterruptJavaScript', result='bool')
    def shouldInterruptJavaScript(self):
        self.callbackLogger.log('*** shouldInterruptJavaScript invoked')
        return True

    def javaScriptAlert(self, frame, msg):
        self.callbackLogger.log('alert from [%s / %s]: %s' % (frame.url(), frame.requestedUrl(), msg))

    def javaScriptConfirm(self, frame, msg):
        self.callbackLogger.log('confirm from [%s / %s]: %s' % (frame.url(), frame.requestedUrl(), msg))
        return False

    def javaScriptPrompt(self, frame, msg, defaultValue, result):
        self.callbackLogger.log('prompt from [%s / %s]: %s' % (frame.url(), frame.requestedUrl(), msg))
        return False

    def javaScriptConsoleMessage(self, message, lineNumber, sourceID):
        self.callbackLogger.log('console log from [%s / %s]: %s' % (lineNumber, sourceID, message))

    def userAgentForUrl(self, url):
        return self.framework.useragent()

    def acceptNavigationRequest(self, frame, request, navType):
        return True
