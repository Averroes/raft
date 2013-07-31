#
# web page handling for spidering
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

from PyQt4.QtCore import Qt, QObject, SIGNAL, QThread, QTimer, QMutex, QUrl
from PyQt4.QtGui import *
from PyQt4 import QtWebKit
from core.web.SpiderWebView import SpiderWebView

class SpiderPageController(QObject):

    PHASE_EXTRACT = 1
    PHASE_MOUSE = 2
    PHASE_TEXT = 3
    PHASE_JAVASCRIPT = 4

    def __init__(self, framework, cookieJar, mainWindow, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework
        self.reset_state(None)
        self.cookieJar = cookieJar
        self.mainWindow = mainWindow
        self.main_tab = None
        self.tab_widget = QTabWidget(self.mainWindow)
        self.tab_widget.setVisible(False)
        
    def add_web_view(self):
        self.main_tab = SpiderWebView(self.framework, self, self.cookieJar, self.mainWindow)
        return self.main_tab

    def clear_windows(self):
        self.tab_widget = QTabWidget(self.mainWindow)
        self.tab_widget.setVisible(False)
        
    def add_window(self):
        widget = QWidget(self.tab_widget)
        web_view = SpiderWebView(self.framework, self, self.cookieJar, widget)
        layout = QVBoxLayout(widget)
        layout.addWidget(web_view)
        return web_view

    def reset_state(self, page_url):
        self.page_url = page_url
        if page_url:
            self.page_url_encoded = str(page_url.toEncoded()).encode('ascii', 'ignore')
        else:
            self.page_url_encoded = ''
        self.phase = self.PHASE_EXTRACT
        self.messages = []
        self.url_links = []
        self.response_ids = []
        self.extraction_finished = False
        self.page_loaded = False

    def set_phase(self, phase):
        self.phase = phase

    def get_phase(self):
        return self.phase

    def advance_phase(self):
        if not self.is_finished():
            self.page_loaded = False
            self.phase += 1

    def phase_extract_links(self):
        return self.phase == self.PHASE_EXTRACT

    def phase_mouse_events(self):
        return self.phase == self.PHASE_MOUSE

    def phase_text_events(self):
        return self.phase == self.PHASE_TEXT

    def phase_javascript_events(self):
        return self.phase == self.PHASE_JAVASCRIPT

    def is_finished(self):
        return self.phase >= self.PHASE_JAVASCRIPT
    
    def set_extraction_finished(self, extraction_finished):
        self.extraction_finished = extraction_finished

    def is_extraction_finished(self):
        return self.extraction_finished

    def log(self, source, url, message):
        self.messages.append((source, url, message))

    def clear_messages(self):
        self.messages = []

    def get_messages(self):
        return self.messages

    def get_url_links(self):
        return self.url_links

    def append_response(self, response_id):
        self.response_ids.append(response_id)

    def get_response_ids(self):
        return self.response_ids

    def acceptNavigation(self, frame, request, navigationType):
        request_url = request.url()
        link = str(request_url.toEncoded()).encode('ascii', 'ignore')
        if frame:
            base_url = str(frame.url().toEncoded()).encode('ascii', 'ignore')
        else:
            base_url = self.page_url_encoded

###        print('got navigation -->', self.page_url, frame, link, navigationType)

        item = (link, base_url)
        if item not in self.url_links:
            self.url_links.append(item)

        if not self.page_loaded and request_url == self.page_url and QtWebKit.QWebPage.NavigationTypeOther == navigationType:
            self.page_loaded = True
            return True

        # if finished with link extraction, allow navigation
        if self.extraction_finished:
            return True

        print('rejected navigation -->', self.page_url, frame, link, navigationType)

        # TODO: allow other?
        return False


        
        
