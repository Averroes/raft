#
# Implements a web page for ODM fuzzing
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

from core.web.BaseWebPage import BaseWebPage

class DomFuzzerWebPage(BaseWebPage):
    def __init__(self, framework, callbackLogger, parent = None):
        BaseWebPage.__init__(self, framework, parent)
        self.framework = framework
        self.callbackLogger = callbackLogger
        self.frameCreated.connect(self.handle_frameCreated)
        self.configure_frame(self.mainFrame())

    def set_page_settings(self, settings):
        # DOM fuzzer is useless without JavaScript enabled
        settings.setAttribute(QtWebKit.QWebSettings.JavascriptEnabled, True)
        settings.setAttribute(QtWebKit.QWebSettings.AutoLoadImages, False)
        settings.setAttribute(QtWebKit.QWebSettings.JavascriptCanOpenWindows, False)

    def handle_frameCreated(self, frame):
        self.configure_frame(frame)

    def configure_frame(self, frame):
        self.add_javascript_window_object(frame)
#        QObject.connect(frame, SIGNAL('loadFinished(bool)'), lambda x: self.handle_frame_loadFinished(frame, x))
        QObject.connect(frame, SIGNAL('javaScriptWindowObjectCleared()'), lambda: self.handle_javaScriptWindowObjectCleared(frame))

    def handle_frame_loadFinished(self, frame, ok):
        print('frame load finished', ok)
        pass

    def handle_javaScriptWindowObjectCleared(self, frame):
        self.add_javascript_window_object(frame)

    def add_javascript_window_object(self, frame):
        frame.addToJavaScriptWindowObject("__RAFT__", self)

    @PyQt4.QtCore.pyqtSlot(name='shouldInterruptJavaScript', result='bool')
    def shouldInterruptJavaScript(self):
        self.callbackLogger.log('console', self.url(), '*** shouldInterruptJavaScript invoked')
        return True

    def javaScriptAlert(self, frame, msg):
        self.callbackLogger.log('alert', frame.url(), msg)

    def javaScriptConfirm(self, frame, msg):
        self.callbackLogger.log('confirm', frame.url(), msg)
        return False

    def javaScriptPrompt(self, frame, msg, defaultValue, result):
        self.callbackLogger.log('prompt', frame.url(),  msg)
        return False

    def javaScriptConsoleMessage(self, message, lineNumber, sourceID):
        self.callbackLogger.log('console', self.mainFrame().url(), 'log from [%s / %s]: %s' % (lineNumber, sourceID, message))

    def userAgentForUrl(self, url):
        return self.framework.useragent()

    def acceptNavigationRequest(self, frame, request, navigationType):
        print('navigation request (%s) -> [%s]' % (navigationType, request.url().toEncoded()))
        # TODO: should other navigation be accepted ?
        if frame and navigationType == QtWebKit.QWebPage.NavigationTypeOther:
            return True
        return True
