#
# Implements the sequence builder web page that has user interaction
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

try:
    from PyQt4.QtCore import QString
except ImportError:
    # we are using Python3 so QString is not defined
    QString = type("")

import uuid
from core.web.BaseWebPage import BaseWebPage

class SequenceBuilderWebPage(BaseWebPage):
    def __init__(self, framework, formCapture, parent = None):
        BaseWebPage.__init__(self, framework, parent)
        self.framework = framework
        self.formCapture = formCapture
        self.loadFinished.connect(self.handle_loadFinished)
        self.frameCreated.connect(self.handle_frameCreated)
        self.contentsChanged.connect(self.handle_contentsChanged)
        self.mainFrame().setProperty('RAFT_requestId', uuid.uuid4().hex)
        self.configure_frame(self.mainFrame())

    def set_page_settings(self, settings):
        # common settings handled by base
        settings.setAttribute(QtWebKit.QWebSettings.JavascriptCanOpenWindows, True)

    def javaScriptConsoleMessage(self, message, lineNumber, sourceID):
        self.framework.console_log('console log from [%s / %s]: %s' % (lineNumber, sourceID, message))

    def userAgentForUrl(self, url):
        return self.framework.useragent()

    def handle_loadFinished(self, ok):
        # TODO: this needs to be moved to frame as well
        frame = self.mainFrame()
        self.add_javascript_window_object(frame)
        self.do_sequence_transition(frame)
        self.input_elements(frame)

    def do_sequence_transition(self, frame):
        previousRequestId = frame.property('RAFT_requestId')
        originatingResponseId = frame.property('RAFT_responseId')
        requestId = uuid.uuid4().hex
        self.formCapture.set_sequence_transition(requestId, originatingResponseId, previousRequestId)
        frame.setProperty('RAFT_requestId', requestId)

    def handle_frameCreated(self, frame):
        frame.setProperty('RAFT_requestId', uuid.uuid4().hex)
        self.configure_frame(frame)

    def configure_frame(self, frame):
        print(('frame configured', frame.property('RAFT_requestId'), frame.property('RAFT_responseId')))
        self.add_javascript_window_object(frame)
        QObject.connect(frame, SIGNAL('loadFinished(bool)'), lambda x: self.handle_frame_loadFinished(frame, x))
        QObject.connect(frame, SIGNAL('javaScriptWindowObjectCleared()'), lambda: self.handle_javaScriptWindowObjectCleared(frame))

    def handle_javaScriptWindowObjectCleared(self, frame):
        self.add_javascript_window_object(frame)

    def add_javascript_window_object(self, frame):
        frame.addToJavaScriptWindowObject("__RAFT__", self)

    def handle_frame_loadFinished(self, frame, ok):
        self.do_sequence_transition(frame)
        self.input_elements(frame)
        print(('frame [%s] load finished (new) (%s)' % (frame.url().toEncoded().data().decode('utf-8'), ok), str(frame.property('RAFT_requestId'))))

    @PyQt4.QtCore.pyqtSlot(QString, int, QVariant, QVariant, QVariant, name='record_input_value')
    def record_input_value(self, requestId, position, name, Type, value):
        self.formCapture.store_source_parameter(str(requestId), position, name, Type, value)

    def handle_contentsChanged(self):
#        print('contents changed', str(self.mainFrame().property('RAFT_requestId').toString()))
        self.process_frame_input_elements(self.mainFrame())

    def acceptNavigationRequest(self, frame, request, navigationType):
        print(('navigation', frame, request, navigationType))

        if frame and navigationType != QtWebKit.QWebPage.NavigationTypeOther:
            self.do_sequence_transition(frame)

        self.input_elements(self.mainFrame())

        # always fetch from network for sequence builder
        request.setAttribute(request.CacheLoadControlAttribute, request.AlwaysNetwork)

        if frame:
            print(('%s->%s' % (frame.property('RAFT_requestId'), request.url().toEncoded().data().decode('utf-8'))))

#        print(['%s:%s' % (str(n), str(request.rawHeader(n))) for n in request.rawHeaderList()])
#        if 'Referer' in [str(n) for n in request.rawHeaderList()]:
#            return False

        return True

    def process_frame_input_elements(self, frame):
        self.input_elements(frame)
        for child in frame.childFrames():
            self.process_frame_input_elements(child)

    def input_elements(self, frame):
        self.formCapture.set_source_url(frame.property('RAFT_requestId'), frame.url().toEncoded().data().decode('utf-8'))
        # TODO: Linux returns the same element repeatedly, so must check processed
        # hopefully gets all of them this way
        processed = []
        element_names = ('input', 'select', 'textarea')
        position = 0
        requestId = ''
        varId = frame.property('RAFT_requestId')
        if varId is not None:
            requestId = str(varId)
        
        for element_name in element_names:
            for input in frame.findAllElements(element_name):
                if input in processed:
                    break
                position += 1
                attrs = [str(x).lower() for x in input.attributeNames()]
                if 'name' in attrs:
                    name_str = "this.name"
                else:
                    name_str = '""'
                if 'type' in attrs:
                    type_str = "this.type"
                else:
                    type_str = '""'
                
                js = 'window.__RAFT__.record_input_value("%s", %d, %s, %s, this.value)' % (requestId, position, name_str, type_str)
#                print(position, input.tagName(), ','.join(attrs), js)
                input.evaluateJavaScript(js)
                processed.append(input)
    
