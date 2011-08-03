#
# implementation for dom fuzzer
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
from PyQt4.QtCore import Qt, QObject, SIGNAL, QUrl, QTimer
from PyQt4.QtGui import *

from core.database.constants import DomFuzzerResultsTable
from core.web.DomFuzzerWebView import DomFuzzerWebView
from widgets.MiniResponseRenderWidget import MiniResponseRenderWidget

class DomFuzzerTab(QObject):

    class CallbackLogger():
        def __init__(self):
            self.messages = []
        def log(self, source, url, message):
            self.messages.append((source, url, message))

        def clear_messages(self):
            self.messages = []

        def get_messages(self):
            return self.messages

    def __init__(self, framework, mainWindow):
        QObject.__init__(self, mainWindow)
        self.framework = framework
        self.mainWindow = mainWindow

        self.mainWindow.domFuzzerStartButton.clicked.connect(self.handle_fuzzerStart_clicked)
        self.mainWindow.domFuzzerStopButton.clicked.connect(self.handle_fuzzerStop_clicked)
        self.mainWindow.domFuzzerClearQueueButton.clicked.connect(self.handle_fuzzerClearQueue_clicked)
        self.mainWindow.domFuzzerStartButton.setEnabled(True)
        self.mainWindow.domFuzzerStopButton.setEnabled(False)

        self.miniResponseRenderWidget = MiniResponseRenderWidget(self.framework, self.mainWindow.domFuzzerResultsTabWidget, self)
        self.mainWindow.domFuzzerResultsTreeView.clicked.connect(self.handle_resultsTreeView_clicked)

        self.setup_fuzz_window()

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def handle_fuzzerStart_clicked(self):
        self.mainWindow.domFuzzerStartButton.setEnabled(False)
        self.mainWindow.domFuzzerStopButton.setEnabled(True)
        self.domFuzzerThread.startFuzzing(self)

    def handle_fuzzerStop_clicked(self):
        self.mainWindow.domFuzzerStartButton.setEnabled(True)
        self.mainWindow.domFuzzerStopButton.setEnabled(False)
        self.domFuzzerThread.stopFuzzing()

    def handle_fuzzerClearQueue_clicked(self):
        self.domFuzzerThread.clearFuzzQueue()

    def setup_fuzz_window(self):
        self.callbackLogger = self.CallbackLogger()
        self.domFuzzerWebView = DomFuzzerWebView(self.framework, self.callbackLogger, self.mainWindow)
        self.domFuzzerPlaceholderLayout = self.mainWindow.domFuzzerFuzzPlaceholder.layout()
        if not self.domFuzzerPlaceholderLayout:
            self.domFuzzerPlaceholderLayout = QVBoxLayout(self.mainWindow.domFuzzerFuzzPlaceholder)
        self.domFuzzerPlaceholderLayout.addWidget(self.domFuzzerWebView)

        self.currentFuzzId = None
        QObject.connect(self.domFuzzerWebView, SIGNAL('loadStarted()'), self.handle_webView_loadStarted)
        QObject.connect(self.domFuzzerWebView, SIGNAL('loadFinished(bool)'), self.handle_webView_loadFinished)

    def set_fuzzer_thread(self, domFuzzerThread):
        self.domFuzzerThread = domFuzzerThread
        QObject.connect(self, SIGNAL('fuzzItemAvailable(int, QString, QUrl)'), self.handle_fuzzItemAvailable)
        QObject.connect(self, SIGNAL('fuzzRunFinished()'), self.handle_fuzzRunFinished)
        self.qtimer = QTimer()
        self.qtimer2 = QTimer()
        QObject.connect(self.qtimer, SIGNAL('timeout()'), self.handle_load_timeout)
        QObject.connect(self.qtimer2, SIGNAL('timeout()'), self.handle_render_timeout)

    def handle_fuzzItemAvailable(self, fuzzId, htmlContent, qurl):
        self.currentFuzzId = fuzzId
        self.currentFuzzUrl = str(qurl.toEncoded())
        self.callbackLogger.clear_messages()
        self.qtimer.start(3000) # 3 seconds to finish
        self.domFuzzerWebView.setHtml(htmlContent, qurl)

    def handle_webView_loadStarted(self):
        print('loading started')

    def handle_webView_loadFinished(self, ok):
        print('handle_webView_loadFinished', ok)
        if self.qtimer.isActive():
            self.qtimer.stop()
        if self.qtimer2.isActive():
            self.qtimer2.stop()
        if ok:
            self.qtimer2.start(1000) # 1 seconds to finish
        else:
            self.fuzzItemCompleted(ok)

    def handle_load_timeout(self):
        if self.qtimer.isActive():
            self.qtimer.stop()
        print('forcbily stopping page')
        self.domFuzzerWebView.stop()
        self.fuzzItemCompleted(False)

    def handle_render_timeout(self):
        if self.qtimer2.isActive():
            self.qtimer2.stop()
        # TODO: should check progress
        self.domFuzzerWebView.stop()
        self.fuzzItemCompleted(True)

    def fuzzItemCompleted(self, ok):
        if self.currentFuzzId is not None:
            mainFrame = self.domFuzzerWebView.page().mainFrame()
            dom = mainFrame.documentElement()
            html = str(dom.toOuterXml().toUtf8()) # TODO: fix encoding issues
            self.domFuzzerThread.fuzzItemFinished(self.currentFuzzId, self.currentFuzzUrl, html, self.callbackLogger.get_messages())
            self.currentFuzzId = None

    def handle_fuzzRunFinished(self):
        self.mainWindow.domFuzzerStartButton.setEnabled(True)
        self.mainWindow.domFuzzerStopButton.setEnabled(False)

    def handle_resultsTreeView_clicked(self):
        index = self.mainWindow.domFuzzerResultsTreeView.currentIndex()
        index = self.mainWindow.domFuzzerResultsDataModel.index(index.row(), DomFuzzerResultsTable.ID)
        if index.isValid():
            currentItem = self.mainWindow.domFuzzerResultsDataModel.data(index)
            if currentItem.isValid():
                fuzzId = str(currentItem.toString())
                self.populate_results_response_render(fuzzId)

    def populate_results_response_render(self, fuzzId):
        results = self.Data.read_dom_fuzzer_results_by_id(self.cursor, int(fuzzId))
        if results:
            resultsItems = [m or '' for m in results]
            self.miniResponseRenderWidget.populate_response_text(
                str(resultsItems[DomFuzzerResultsTable.URL]),
                '',
                str(resultsItems[DomFuzzerResultsTable.RENDERED_DATA]),
                ''
                )
                
