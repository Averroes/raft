#
# crawler tab implementation
#
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

from core.crawler.SpiderPageController import SpiderPageController
from core.network.InMemoryCookieJar import InMemoryCookieJar

class CrawlerTab(QObject):

    def __init__(self, framework, mainWindow):
        QObject.__init__(self, mainWindow)
        self.framework = framework
        self.mainWindow = mainWindow

        self.mainWindow.crawlerSpiderSequenceCheckBox.stateChanged.connect(self.handle_crawlerSpiderSequenceCheckBox_stateChanged)
        self.mainWindow.crawlerSpiderStartButton.clicked.connect(self.handle_spiderStart_clicked)
        self.mainWindow.crawlerSpiderStopButton.clicked.connect(self.handle_spiderStop_clicked)
        self.mainWindow.crawlerSpiderClearQueueButton.clicked.connect(self.handle_spiderClearQueue_clicked)
        self.mainWindow.crawlerSpiderPendingResponsesClearButton.clicked.connect(self.handle_spiderClearPendingResponses_clicked)
        self.mainWindow.crawlerSpiderPendingResponsesResetButton.clicked.connect(self.handle_spiderResetPendingResponses_clicked)
        self.mainWindow.crawlerSpiderStartButton.setEnabled(True)
        self.mainWindow.crawlerSpiderStopButton.setEnabled(False)

        self.setup_spider_window()

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)
        self.framework.subscribe_sequences_changed(self.fill_sequences)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.fill_sequences()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def fill_sequences(self):
        self.fill_sequences_combo_box(self.mainWindow.crawlerSpiderSequenceComboBox)

    def fill_sequences_combo_box(self, comboBox):
        selectedText = comboBox.currentText()

        comboBox.clear()
        for row in self.Data.get_all_sequences(self.cursor):
            sequenceItem = [m or '' for m in row]
            name = str(sequenceItem[1])
            Id = str(sequenceItem[0])
            item = comboBox.addItem(name, Id)

        if selectedText:
            index = comboBox.findText(selectedText)
            if index != -1:
                comboBox.setCurrentIndex(index)

    def handle_crawlerSpiderSequenceCheckBox_stateChanged(self, state):
        self.mainWindow.crawlerSpiderSequenceComboBox.setEnabled(self.mainWindow.crawlerSpiderSequenceCheckBox.isChecked())

    def handle_spiderStart_clicked(self):
        self.mainWindow.crawlerSpiderStartButton.setEnabled(False)
        self.mainWindow.crawlerSpiderStopButton.setEnabled(True)
        sequenceId = None
        if self.mainWindow.crawlerSpiderSequenceCheckBox.isChecked():
            sequenceId = int(self.mainWindow.crawlerSpiderSequenceComboBox.itemData(self.mainWindow.crawlerSpiderSequenceComboBox.currentIndex()))
        self.spiderThread.startSpidering(self, sequenceId, self.cookieJar)

    def handle_spiderStop_clicked(self):
        self.mainWindow.crawlerSpiderStartButton.setEnabled(True)
        self.mainWindow.crawlerSpiderStopButton.setEnabled(False)
        self.spiderThread.stopSpidering()

    def handle_spiderClearQueue_clicked(self):
        self.spiderThread.clearSpiderQueue()

    def handle_spiderClearPendingResponses_clicked(self):
        self.spiderThread.clearSpiderPendingResponses()

    def handle_spiderResetPendingResponses_clicked(self):
        self.spiderThread.resetSpiderPendingResponses()

    def set_spider_thread(self, spiderThread):
        self.spiderThread = spiderThread
        QObject.connect(self, SIGNAL('spiderRunFinished()'), self.handle_spiderRunFinished)
        QObject.connect(self, SIGNAL('spiderItemAvailable(int, QString, QUrl, int)'), self.handle_spiderItemAvailable)
        self.spider_qtimer = QTimer()
        self.spider_qtimer2 = QTimer()
        QObject.connect(self.spider_qtimer, SIGNAL('timeout()'), self.handle_spider_load_timeout)
        QObject.connect(self.spider_qtimer2, SIGNAL('timeout()'), self.handle_spider_render_timeout)

    def setup_spider_window(self):
        self.cookieJar = InMemoryCookieJar(self.framework, self)
        self.spiderPageController = SpiderPageController(self.framework, self.cookieJar, self.mainWindow, self)
        self.spiderConfig = self.framework.getSpiderConfig()

        self.crawlerSpiderWebView = self.spiderPageController.add_web_view()
        self.crawlerSpiderPlaceholderLayout = self.mainWindow.crawlerSpiderWindowPlaceholder.layout()
        if not self.crawlerSpiderPlaceholderLayout:
            self.crawlerSpiderPlaceholderLayout = QVBoxLayout(self.mainWindow.crawlerSpiderWindowPlaceholder)
        self.crawlerSpiderPlaceholderLayout.addWidget(self.crawlerSpiderWebView)
        
        self.currentSpiderId = None
        self.currentHtmlContent = None
        self.currentQUrl = None

        QObject.connect(self.crawlerSpiderWebView, SIGNAL('loadStarted()'), self.handle_spiderWebView_loadStarted)
        QObject.connect(self.crawlerSpiderWebView, SIGNAL('loadFinished(bool)'), self.handle_spiderWebView_loadFinished)

    def handle_spiderRunFinished(self):
        self.mainWindow.crawlerSpiderStartButton.setEnabled(True)
        self.mainWindow.crawlerSpiderStopButton.setEnabled(False)

    def handle_spiderItemAvailable(self, spiderId, htmlContent, qurl, depth):
        self.currentSpiderId = spiderId
        self.currentHtmlContent = htmlContent
        self.currentQUrl = qurl
        self.currentDepth = depth
        self.currentSpiderUrl = qurl.toEncoded().data().decode('utf-8')
        self.spiderPageController.reset_state(qurl)
        self.load_html_content()

    def load_html_content(self):
        self.spider_qtimer.start(3000) # 3 seconds to finish
        self.crawlerSpiderWebView.setHtml(self.currentHtmlContent, self.currentQUrl)

    def handle_spiderWebView_loadStarted(self):
        print(('spider web loading started: %s' % (self.spiderPageController.get_phase())))

    def handle_spiderWebView_loadFinished(self, ok):
        print(('spider web loading finished [%s]: %s' % (ok, self.spiderPageController.get_phase())))
        if self.spider_qtimer.isActive():
            self.spider_qtimer.stop()
        if self.spider_qtimer2.isActive():
            self.spider_qtimer2.stop()
        if ok:
            self.spider_qtimer2.start(1000) # 1 seconds to finish
        else:
            self.spiderItemCompleted(ok)

    def handle_spider_load_timeout(self):
        if self.spider_qtimer.isActive():
            self.spider_qtimer.stop()
        print('forcbily stopping page')
        self.crawlerSpiderWebView.stop()
        self.spiderItemCompleted(False)

    def handle_spider_render_timeout(self):
        if self.spider_qtimer2.isActive():
            self.spider_qtimer2.stop()
        # TODO: should check progress
        self.crawlerSpiderWebView.stop()
        self.spiderItemCompleted(True)

    def spiderItemCompleted(self, ok):
        webPage = self.crawlerSpiderWebView.page()
        mainFrame = webPage.mainFrame()
        if not self.spiderPageController.is_extraction_finished():
            self.process_page_events(webPage, mainFrame)
            self.process_frame_content(mainFrame)
        if self.spiderConfig.evaluate_javascript:
            if not self.spiderPageController.is_finished():
                self.spiderPageController.advance_phase()
                # TODO: should this be signal emitted via one-shot timer ?
                self.load_html_content()
            else:
                self.finish_spider_item()
        else:
            self.finish_spider_item()

    def finish_spider_item(self):
        for link, base_url in self.spiderPageController.get_url_links():
            self.spiderThread.process_page_url_link(link, base_url, self.currentDepth)
        for response_id in self.spiderPageController.get_response_ids():
            self.spiderThread.process_page_response_id(response_id, self.currentDepth)

        self.crawlerSpiderWebView.cleanup()
        self.spiderThread.spiderItemFinished(self.currentSpiderId)

    def process_page_events(self, webPage, frame):
        try:
            webPage.process_page_events(frame)
            for child in frame.childFrames():
                self.process_page_events(webPage, child)
        except Exception as error:
            self.framework.report_exception(error)

    def process_frame_content(self, frame):
        self.extract_frame_content(frame)
        for child in frame.childFrames():
            self.process_frame_content(child)

    def extract_frame_content(self, frame):
        parentFrame = frame.parentFrame()
        if parentFrame:
            referer = parentFrame.url().toEncoded().data().decode('utf-8')
        else:
            referer = self.currentSpiderUrl
        dom = frame.documentElement()
        html = dom.toOuterXml()
        url = frame.url().toEncoded().data().decode('utf-8')
        self.spiderThread.process_page_html_content(html, url, self.currentDepth)

