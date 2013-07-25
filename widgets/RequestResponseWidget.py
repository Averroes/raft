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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from PyQt4 import QtWebKit, QtNetwork, Qsci

from io import StringIO
from urllib import parse as urlparse
import traceback

from utility import ContentHelper

from core.web.RenderingWebView import RenderingWebView
from core.web.StandardPageFactory import StandardPageFactory
from core.web.HeadlessPageFactory import HeadlessPageFactory

from core.database.constants import ResponsesTable

class RequestResponseWidget(QObject):
    def __init__(self, framework, tabwidget, searchControlPlaceholder, parent = None):

        QObject.__init__(self, parent)

        self.framework = framework
        self.standardPageFactory = StandardPageFactory(self.framework, None, self)
        self.headlessPageFactory = HeadlessPageFactory(self.framework, None, self)

        self.qlock = QMutex()

        self.contentExtractor = self.framework.getContentExtractor()
        self.htmlExtractor = self.contentExtractor.getExtractor('html')

        self.contentTypeMapping = {
            # TODO: complete
            'json' : 'javascript',
            'javascript': 'javascript',
            'text/x-js' : 'javascript',
            'html' : 'html',
            'text/xml' : 'xml',
            'text/html' : 'html',
            'text/xhtml' : 'html',
            'text/css' : 'css',
            'text/plain' : 'text',
            }
        self.lexerMapping = {
            'text' : None,
            'javascript' : Qsci.QsciLexerJavaScript,
            'html' : Qsci.QsciLexerHTML,
            'xml' : Qsci.QsciLexerXML,
            'css' : Qsci.QsciLexerCSS,
            }

        self.setup_ui(tabwidget, searchControlPlaceholder)

        self.Data = None
        self.cursor = None
        self.requestResponse = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.clear()

    def db_detach(self):
        self.close_cursor()
        self.Data = None
        self.clear()

    def close_cursor(self):
        if self.cursor:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def setup_ui(self, tabwidget, searchControlPlaceholder):

        self.tabwidget = tabwidget
        self.searchControlPlaceholder = searchControlPlaceholder

        self.networkAccessManager = self.framework.getNetworkAccessManager()

        if self.searchControlPlaceholder is not None:
            self.searchLayout = self.searchControlPlaceholder.layout()
            if not self.searchLayout or 0 == self.searchLayout:
                self.searchLayout = QVBoxLayout(self.searchControlPlaceholder)
            self.searchLayout.addWidget(self.makeSearchWidget(self.searchControlPlaceholder))
            self.searchLayout.addWidget(self.makeConfirmedUpdateWidget(self.searchControlPlaceholder))
            self.searchLayout.setSpacing(0)
            self.searchLayout.setContentsMargins(-1, 0, -1, 0)
            self.searchControlPlaceholder.updateGeometry()

        self.requestView = QWidget(tabwidget)
        self.requestView.setObjectName(tabwidget.objectName()+'Request')
        self.tabwidget.addTab(self.requestView, 'Request')

        self.responseView = QWidget(tabwidget)
        self.responseView.setObjectName(tabwidget.objectName()+'Response')
        self.tabwidget.addTab(self.responseView, 'Response')

        self.scriptsView = QWidget(tabwidget)
        self.scriptsView.setObjectName(tabwidget.objectName()+'Scripts')
        self.scriptsTabIndex = self.tabwidget.addTab(self.scriptsView, 'Scripts')

        self.commentsView = QWidget(tabwidget)
        self.commentsView.setObjectName(tabwidget.objectName()+'Comments')
        self.tabwidget.addTab(self.commentsView, 'Comments')

        self.linksView = QWidget(tabwidget)
        self.linksView.setObjectName(tabwidget.objectName()+'Links')
        self.tabwidget.addTab(self.linksView, 'Links')

        self.formsView = QWidget(tabwidget)
        self.formsView.setObjectName(tabwidget.objectName()+'Forms')
        self.tabwidget.addTab(self.formsView, 'Forms')

        self.renderView = QWidget(tabwidget)
        self.renderView.setObjectName(tabwidget.objectName()+'Render')
        self.renderTabIndex = self.tabwidget.addTab(self.renderView, 'Render')
        self.tabwidget.currentChanged.connect(self.handle_tab_currentChanged)

        self.generatedSourceView = QWidget(tabwidget)
        self.generatedSourceView.setObjectName(tabwidget.objectName()+'GeneratedSource')
        self.generatedSourceTabIndex = self.tabwidget.addTab(self.generatedSourceView, 'Generated Source')

        self.notesView = QWidget(tabwidget)
        self.notesView.setObjectName(tabwidget.objectName()+'Notes')
        self.notesTabIndex = self.tabwidget.addTab(self.notesView, 'Notes')

        self.tab_item_widgets = []

        self.vlayout0 = QVBoxLayout(self.requestView)
        self.requestScintilla = Qsci.QsciScintilla(self.requestView)
        self.setScintillaProperties(self.requestScintilla)
        self.vlayout0.addWidget(self.requestScintilla)
        self.tab_item_widgets.append(self.requestScintilla)

        self.vlayout1 = QVBoxLayout(self.responseView)
        self.responseScintilla = Qsci.QsciScintilla(self.responseView)
        self.responseScintilla.setMarginLineNumbers(1, True)
        self.setScintillaProperties(self.responseScintilla)
        self.vlayout1.addWidget(self.responseScintilla)
        self.tab_item_widgets.append(self.responseScintilla)

        self.vlayout2 = QVBoxLayout(self.scriptsView)
        self.scriptsScintilla = Qsci.QsciScintilla(self.scriptsView)
#        self.scriptsScintilla.setMarginLineNumbers(1, True)
        self.setScintillaProperties(self.scriptsScintilla, 'javascript')
        self.vlayout2.addWidget(self.scriptsScintilla)
        self.tab_item_widgets.append(self.scriptsScintilla)

        self.vlayout3 = QVBoxLayout(self.commentsView)
        self.commentsScintilla = Qsci.QsciScintilla(self.commentsView)
#        self.commentsScintilla.setMarginLineNumbers(1, True)
        self.setScintillaProperties(self.commentsScintilla, 'html')
        self.vlayout3.addWidget(self.commentsScintilla)
        self.tab_item_widgets.append(self.commentsScintilla)

        self.vlayout4 = QVBoxLayout(self.linksView)
        self.linksScintilla = Qsci.QsciScintilla(self.linksView)
        self.setScintillaProperties(self.linksScintilla)
        self.vlayout4.addWidget(self.linksScintilla)
        self.tab_item_widgets.append(self.linksScintilla)

        self.vlayout5 = QVBoxLayout(self.formsView)
        self.formsScintilla = Qsci.QsciScintilla(self.formsView)
        self.setScintillaProperties(self.formsScintilla, 'html')
        self.vlayout5.addWidget(self.formsScintilla)
        self.tab_item_widgets.append(self.formsScintilla)

        self.vlayout6 = QVBoxLayout(self.renderView)
        self.renderWebView = RenderingWebView(self.framework, self.standardPageFactory, self.renderView)
        self.renderWebView.page().setNetworkAccessManager(self.networkAccessManager)
        self.renderWebView.loadFinished.connect(self.render_handle_loadFinished)
        self.vlayout6.addWidget(self.renderWebView)
        self.tab_item_widgets.append(self.renderWebView)

        self.vlayout7 = QVBoxLayout(self.generatedSourceView)
        self.generatedSourceScintilla = Qsci.QsciScintilla(self.generatedSourceView)
        self.generatedSourceWebView = RenderingWebView(self.framework, self.headlessPageFactory, self.generatedSourceView)
        self.generatedSourceWebView.page().setNetworkAccessManager(self.networkAccessManager)
        self.generatedSourceWebView.loadFinished.connect(self.generatedSource_handle_loadFinished)
        self.generatedSourceWebView.setVisible(False)
        self.generatedSourceScintilla.setMarginLineNumbers(1, True)
        self.setScintillaProperties(self.generatedSourceScintilla, 'html')
        self.vlayout7.addWidget(self.generatedSourceWebView)
        self.vlayout7.addWidget(self.generatedSourceScintilla)
        self.tab_item_widgets.append(self.generatedSourceScintilla)

        self.vlayout8 = QVBoxLayout(self.notesView)
        self.notesTextEdit = QTextEdit(self.notesView)
        self.vlayout8.addWidget(self.notesTextEdit)
        self.tab_item_widgets.append(self.notesTextEdit)

        self.clear()

    def setScintillaProperties(self, scintillaWidget, contentType = 'text'):
        scintillaWidget.setFont(self.framework.get_font())
        scintillaWidget.setWrapMode(1)
        scintillaWidget.zoomTo(self.framework.get_zoom_size())
        # TOOD: set based on line numbers (size is in pixels)
        scintillaWidget.setMarginWidth(1, '1000')
        self.attachLexer(scintillaWidget, contentType)
        self.framework.subscribe_zoom_in(lambda: scintillaWidget.zoomIn())
        self.framework.subscribe_zoom_out(lambda: scintillaWidget.zoomOut())
        
    def makeSearchWidget(self, parentWidget, tooltip = 'Search the value'):
        # TODO: these should be store in a class variable list to so that they can be cleared...
        self.searchWidget = QWidget(parentWidget)
        self.searchWidget.setContentsMargins(-1, 0, -1, 0)
        self.search_hlayout = QHBoxLayout(self.searchWidget)
        self.search_label = QLabel(self.searchWidget)
        self.search_label.setText('Search: ')
        self.searchLineEdit = QLineEdit(self.searchWidget)
        self.searchLineEdit.setToolTip(tooltip)
        self.search_hlayout.addWidget(self.search_label)
        self.search_hlayout.addWidget(self.searchLineEdit)
        # always supports regex search
        self.searchReCheckBox = QCheckBox(self.searchWidget)
        self.searchReCheckBox.setText('RE')
        self.searchReCheckBox.setToolTip('Use Regular Expression Syntax')
        self.search_hlayout.addWidget(self.searchReCheckBox)
        self.searchFindButton = QPushButton()
        self.searchFindButton.setText('Find')
        QObject.connect(self.searchFindButton, SIGNAL('clicked()'), self.run_search_find)
        QObject.connect(self.searchLineEdit, SIGNAL('returnPressed()'), self.run_search_find)
        self.search_hlayout.addWidget(self.searchFindButton)
        return self.searchWidget

    def run_search_find(self):
        targetWidget = self.tab_item_widgets[self.tabwidget.currentIndex()]
        if isinstance(targetWidget, Qsci.QsciScintilla):
            self.searchScintilla(targetWidget)
        elif isinstance(targetWidget,  QtWebKit.QWebView):
            self.searchWebView(targetWidget)
        else:
            self.searchTextEdit(targetWidget)

    def confirmedButtonStateChanged(self, state):
        # self.emit(SIGNAL('confirmedButtonSet(int)'), state)
        if hasattr(self, 'confirmedCheckBox'):
            self.confirmedCheckBox.setChecked(state)

    def makeConfirmedUpdateWidget(self, parentWidget):
        self.confirmedUpdateWidget = QWidget(parentWidget)
        self.confirmedUpdateWidget.setContentsMargins(-1, 0, -1, 0)
        self.confirmed_hlayout = QHBoxLayout(self.confirmedUpdateWidget)
        self.confirmedCheckBox = QCheckBox(parentWidget)
        self.confirmedCheckBox.setText('Confirmed Vulnerable')
        QObject.connect(self.confirmedCheckBox, SIGNAL('stateChanged(int)'), self.confirmedButtonStateChanged)
        self.quickNotesLabel = QLabel(parentWidget)
        self.quickNotesLabel.setText('Quick Notes: ')
        self.quickNotesEdit = QLineEdit(parentWidget)
        self.confirmed_horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.updateButton = QPushButton(parentWidget)
        self.updateButton.setText('Update')
        QObject.connect(self.updateButton, SIGNAL('clicked()'), self.handle_updateButton_clicked)
        self.confirmed_hlayout.addWidget(self.confirmedCheckBox)
        self.confirmed_hlayout.addItem(self.confirmed_horizontalSpacer)
        self.confirmed_hlayout.addWidget(self.quickNotesLabel)
        self.confirmed_hlayout.addWidget(self.quickNotesEdit)
        self.confirmed_hlayout.addWidget(self.updateButton)
        return self.confirmedUpdateWidget

    def handle_updateButton_clicked(self):
        if self.responseId is not None:
            quickNotes = str(self.quickNotesEdit.text()).strip()
            notes = str(self.notesTextEdit.toPlainText())
            confirmed = str(self.confirmedCheckBox.isChecked())
            if len(quickNotes) > 0:
                notes = quickNotes + '\n' + notes
            self.Data.update_responses(self.cursor, notes, '', confirmed, self.responseId)
            self.quickNotesEdit.setText('')
            self.notesTextEdit.setText(notes)
            # update request response state
            self.requestResponse.confirmed = confirmed
            self.requestResponse.notes = notes
            # TODO: update in datamodel

    def searchTextEdit(self, targetWidget):
        # TODO: simulate regex searching
        searchText = self.searchLineEdit.text()
        return targetWidget.find(searchText)

    def searchScintilla(self, targetWidget):
        searchText = self.searchLineEdit.text()
        line, index = targetWidget.getCursorPosition()
        return targetWidget.findFirst(searchText, self.searchReCheckBox.isChecked(), False, False, True, True, line, index)

    def searchWebView(self, targetWidget):
        is_re = self.searchReCheckBox.isChecked()
        searchText = self.searchLineEdit.text()
        # TODO: simulate regex search
        targetWidget.findText('', QtWebKit.QWebPage.FindWrapsAroundDocument|QtWebKit.QWebPage.HighlightAllOccurrences)
        return targetWidget.findText(searchText, QtWebKit.QWebPage.FindWrapsAroundDocument|QtWebKit.QWebPage.HighlightAllOccurrences)

    def viewItemSelected(self, index):
        if index and index.isValid():
            obj = index.internalPointer()
            self.fill(obj.Id)

    def clear(self):
        # clear
        self.responseId = None
        self.requestResponse = None
        self.requestScintilla.setText('')
        self.responseScintilla.setText('')
        self.scriptsScintilla.setText('')
        self.commentsScintilla.setText('')
        self.linksScintilla.setText('')
        self.formsScintilla.setText('')
        self.renderWebView.setHtml('')
        self.generatedSourceWebView.setHtml('')
        self.generatedSourceScintilla.setText('')
        self.contentResults = None
        self.notesTextEdit.setPlainText('')
        self.confirmedButtonStateChanged(Qt.Unchecked)

    def set_search_info(self, searchText, isRE):
        self.searchLineEdit.setText(searchText)
        self.searchReCheckBox.setChecked(isRE)

    def fill(self, Id):
        if self.requestResponse and self.requestResponse.Id == Id:
            # already filled
            return

        if self.qlock.tryLock():
            try:
                self.fill_internal(Id)
            finally:
                self.qlock.unlock()

    def fill_internal(self, Id):

        self.clear()

        if not Id:
            return

        self.responseId = Id
        self.requestResponse = self.framework.get_request_response(Id)
        rr = self.requestResponse

        confirmedState = Qt.Unchecked
        if rr.confirmed and rr.confirmed.lower() in ['y', '1', 'true']:
            confirmedState = Qt.Checked
        self.confirmedButtonStateChanged(confirmedState)

        self.requestScintilla.setText(rr.rawRequest)

        self.attachLexer(self.responseScintilla, rr.responseContentType, rr.responseBody)
        self.responseScintilla.setText(ContentHelper.convertBytesToDisplayText(rr.rawResponse))
        self.contentResults = self.generateExtractorResults(rr.responseHeaders, rr.responseBody, rr.responseUrl, rr.charset)
        self.notesTextEdit.setText(rr.notes)
        self.handle_tab_currentChanged(self.tabwidget.currentIndex())

    def generateExtractorResults(self, headers, body, url, charset):
        rr = self.requestResponse
        scriptsIO, commentsIO, linksIO, formsIO = StringIO(), StringIO(), StringIO(), StringIO()
        try:
            # include any Location or Content-Location responses in links
            # TODO: refactor the extracted content so it is universally available via RequestResponse object
            # TODO: duplicate links may be output depending on redirect response content
            for line in headers.splitlines():
                if b':' in line:
                    name, value = [m.strip() for m in line.split(b':', 1)]
                    if name.lower() in (b'location', b'content-location'):
                        link = value.decode('utf-8', 'ignore')
                        url = urlparse.urljoin(url, link)
                        linksIO.write('%s\n' % url)

            results = rr.results
            if 'html' == rr.baseType:
                # Create content for parsing HTML
                self.htmlExtractor.process(body, url, charset, results)

                self.tabwidget.setTabText(self.scriptsTabIndex, 'Scripts')
                for script in results.scripts:
                    scriptsIO.write('%s\n\n' % self.flat_str(script))

                self.attachLexer(self.commentsScintilla, 'html')
                for comment in results.comments:
                    commentsIO.write('%s\n\n' % self.flat_str(comment))

                for link in results.links:
                    linksIO.write('%s\n' % self.flat_str(link))

                for form in results.forms:
                    formsIO.write('%s\n' % self.flat_str(form))

                for input in results.other_inputs:
                    formsIO.write('%s\n' % self.flat_str(input))

            elif 'javascript' == rr.baseType:

                self.tabwidget.setTabText(self.scriptsTabIndex, 'Strings')
                for script_string in results.strings:
                    scriptsIO.write('%s\n' % self.flat_str(script_string))

                self.attachLexer(self.commentsScintilla, 'javascript')
                for comment in results.comments:
                    commentsIO.write('%s\n' % self.flat_str(comment))

                for link in results.links:
                    linksIO.write('%s\n' % self.flat_str(link))

                for link in results.relative_links:
                    linksIO.write('%s\n' % self.flat_str(link))

        except Exception as e:
            # TODO: log 
            self.framework.report_exception(e)

        self.scriptsScintilla.setText(scriptsIO.getvalue())
        self.commentsScintilla.setText(commentsIO.getvalue())
        self.linksScintilla.setText(linksIO.getvalue())
        self.formsScintilla.setText(formsIO.getvalue())

    def flat_str(self, u):
        if bytes == type(u):
            try:
                s = u.decode('utf-8')
            except UnicodeDecodeError:
                s = repr(u)[2:-1].replace('\\r', '').replace('\\n', '\n').replace('\\t', '\t')

            return s
        else:
            # may be object type implementing str
            s = str(u)
            return s

    def attachLexer(self, scintillaWidget, contentType, data = ''):
        lexer = self.getLexer(contentType, data)
        if lexer:
            lexerInstance = lexer(scintillaWidget)
            lexerInstance.setFont(self.framework.get_font())
            scintillaWidget.setLexer(lexerInstance)
        else:
            scintillaWidget.setLexer(None)

    def handle_tab_currentChanged(self, index):
        if index == self.renderTabIndex:
            return self.doRenderApply()
        elif index == self.generatedSourceTabIndex:
            return self.doGeneratedSourceApply()
        return False
        
    def doRenderApply(self):
        rr = self.requestResponse
        if rr and rr.responseUrl:
            self.renderWebView.fill_from_response(rr.responseUrl, rr.responseHeaders, rr.responseBody, rr.responseContentType)
            return True
        return False

    def doGeneratedSourceApply(self):
        rr = self.requestResponse
        if rr and rr.responseUrl and 'html' == rr.baseType:
            self.generatedSourceWebView.fill_from_response(rr.responseUrl, rr.responseHeaders, rr.responseBody, rr.responseContentType)
            return True
        return False

    def generatedSource_handle_loadFinished(self):
        self.set_generated_source(self.generatedSourceWebView)

    def render_handle_loadFinished(self):
        self.set_generated_source(self.renderWebView)

    def set_generated_source(self, webview):
        # TODO: consider merging frames sources?
        # TODO: consider other optimizations
        if self.requestResponse:
            rr = self.requestResponse
            xhtml = webview.page().mainFrame().documentElement().toOuterXml()
            self.generatedSourceScintilla.setText(xhtml)
            body_bytes = xhtml.encode('utf-8')
            self.generateExtractorResults(rr.responseHeaders, body_bytes, rr.responseUrl, rr.charset)

    def getLexer(self, contentType, data):
        lexerContentType = self.inferContentType(contentType, data)
        return self.lexerMapping[lexerContentType]
        
    def inferContentType(self, contentType, data):
        # TODO: scan data for additional info
        # XXX: data -> bytes
        for comp in list(self.contentTypeMapping.keys()):
            if comp in contentType:
                return self.contentTypeMapping[comp]
        return 'text'
            
    def set_search(self, tabname, searchText):
        if tabname == 'request':
            self.tabwidget.setCurrentIndex(0)
        elif tabname=='response':
            self.tabwidget.setCurrentIndex(1)
        self.searchLineEdit.setText(searchText)
        self.requestScintilla.findFirst(searchText, False, True, False, True)
        self.responseScintilla.findFirst(searchText, False, True, False, True)

         
        
  
