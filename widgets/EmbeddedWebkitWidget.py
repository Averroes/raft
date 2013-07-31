#
# Implements a embedded browser widget
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

from core.web.CustomWebView import CustomWebView
import uuid

# TODO: implement logging framework
class StdoutLogger():
    def __init__(self):
        pass
    def log(self, *msg):
        print(msg)

class EmbeddedWebkitWidget(QObject):
    def __init__(self, framework, networkAccessManager, pageFactory, displayWidget, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework
        self.networkAccessManager = networkAccessManager
        self.pageFactory = pageFactory
        self.displayWidget = displayWidget 
        self.vlayout0 = self.displayWidget.layout()
        if not self.vlayout0:
            self.vlayout0 = QVBoxLayout(self.displayWidget)
        self.hbox = QHBoxLayout()
        self.urlEntryEdit = QLineEdit(self.displayWidget)
        self.urlEntryEdit.setObjectName('urlEntryEdit')
        self.actionButton = QPushButton(self.displayWidget)
        self.actionButton.setText('Go')
        self.actionButton.setObjectName('actionButton')
        self.actionButton.clicked.connect(self.action_button_clicked)
        self.hbox.addWidget(self.urlEntryEdit)
        self.hbox.addWidget(self.actionButton)
        self.tabWidget = QTabWidget(self.displayWidget)
        self.tabWidget.setTabsClosable(True)

        self.progressBar = QProgressBar(self.displayWidget)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)

        self.vlayout0.addItem(self.hbox)
        self.vlayout0.addWidget(self.tabWidget)
        self.vlayout0.addWidget(self.progressBar)

        self.browserTabs = {}
        self.tabs = []

        self.tabWidget.tabCloseRequested.connect(self.tab_close_requested)
        self.tabWidget.currentChanged.connect(self.current_tab_changed)

    def set_url_edit_text(self, browserTab):
        url = str(browserTab.url().toEncoded())
        if url == 'about:blank':
            self.urlEntryEdit.setText('')
        else:
            self.urlEntryEdit.setText(url)
            self.urlEntryEdit.setCursorPosition(0)

    def tab_close_requested(self, index):
        if index >= len(self.tabs):
            return
        self.tabWidget.removeTab(index)
        tab_id = self.tabs.pop(index)
        if self.browserTabs.has_key(tab_id):
            browserTab = self.browserTabs[tab_id]
            self.browserTabs.pop(tab_id)
            browserTab.stop()

    def current_tab_changed(self, index):
        if index >= len(self.tabs):
            return
        tab_id = self.tabs[index]
        if self.browserTabs.has_key(tab_id):
            browserTab = self.browserTabs[tab_id]
            self.currentTab = browserTab
            self.set_url_edit_text(self.currentTab)
            finished, progress, title = self.currentTab.get_status()
            if finished or 100 == progress:
                self.actionButton.setText('Go')
            else:
                self.actionButton.setText('Stop')
            self.progressBar.setValue(progress)
            self.tabWidget.setTabText(index, title)

    def add_browser_tab(self):
        tab_id = uuid.uuid4().hex
        widget = QWidget(self.tabWidget)
        widget.setObjectName('tab_%s' % tab_id)
        layout = QVBoxLayout(widget)
        browserTab = CustomWebView(self, tab_id, widget)
        browserTab.setPage(self.pageFactory.new_page(browserTab))
        # TODO: should page factory set network access manager?
        browserTab.page().setNetworkAccessManager(self.networkAccessManager)
        layout.addWidget(browserTab)

        self.tabWidget.addTab(widget, 'New Tab')
        self.browserTabs[tab_id] = browserTab
        self.tabs.append(tab_id)
        return browserTab

    def action_button_clicked(self):
        if 0 == len(self.tabs):
            self.currentTab = self.add_browser_tab()
        if 'Stop' == self.actionButton.text():
            self.currentTab.stop()
            self.actionButton.setText('Go')
            return
        url = self.urlEntryEdit.text()
        qurl = QUrl.fromUserInput(url)
        if qurl.isValid():
            self.currentTab.setUrl(qurl)
            self.actionButton.setText('Stop')

    def browser_load_started(self, tab_id):
        browserTab = self.browserTabs[tab_id]
        if browserTab == self.currentTab:
            pass
        
    def browser_load_finished(self, tab_id):
        browserTab = self.browserTabs[tab_id]
        if browserTab == self.currentTab:
            self.actionButton.setText('Go')

    def browser_url_changed(self, tab_id):
        browserTab = self.browserTabs[tab_id]
        if browserTab == self.currentTab:
            self.set_url_edit_text(self.currentTab)

    def browser_title_changed(self, tab_id, title):
        if tab_id in self.tabs:
            index = self.tabs.index(tab_id)
            self.tabWidget.setTabText(index, title)

    def browser_load_progress(self, tab_id, progress):
        browserTab = self.browserTabs[tab_id]
        if browserTab == self.currentTab:
            if 100 == progress:
                self.actionButton.setText('Go')
            self.progressBar.setValue(progress)
        
