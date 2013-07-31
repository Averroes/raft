#
# Implements a custom web view widget
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
from PyQt4.QtGui import *

class CustomWebView(QtWebKit.QWebView):
    def __init__(self, browser, tab_id, parent = None):
        QtWebKit.QWebView.__init__(self, parent)
        self.browser = browser
        self.tab_id = tab_id

        self.is_finished = True
        self.progress = 0
        self.title = ''

        self.loadStarted.connect(self.tab_load_started)
        self.loadFinished.connect(self.tab_load_finished)
        self.urlChanged.connect(self.tab_url_changed)
        self.loadProgress.connect(self.tab_load_progress)
        self.titleChanged.connect(self.tab_title_changed)

    def createWindow(self, windowType):
        tab = self.browser.add_browser_tab()
        return tab

    def tab_load_started(self):
        self.is_finished = False
        self.browser.browser_load_started(self.tab_id)
        
    def tab_load_finished(self):
        self.is_finished = True
        self.browser.browser_load_finished(self.tab_id)

    def tab_url_changed(self):
        self.browser.browser_url_changed(self.tab_id)

    def tab_load_progress(self, progress):
        self.progress = progress
        self.browser.browser_load_progress(self.tab_id, progress)

    def tab_title_changed(self, title):
        self.title = title
        self.browser.browser_title_changed(self.tab_id, title)

    def get_status(self):
        return (self.is_finished, self.progress, self.title)
