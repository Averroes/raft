#
# Sequence builder dialog
#
# Authors: 
#          Gregory Fleischer (gfleischer@gmail.com)
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

from PyQt4.QtCore import (Qt, SIGNAL, QObject, pyqtSignature, QUrl, QSettings, QDir, QThread, QMutex)
from PyQt4.QtGui import *
from PyQt4 import Qsci
from PyQt4. QtNetwork import *

from ui import SequenceDialog
import re
import time
import json

from widgets import EmbeddedWebkitWidget
from utility import ContentHelper
from actions import interface

from core.web.SequenceBuilderPageFactory import SequenceBuilderPageFactory
from core.web.SequenceBuilderFormCapture import SequenceBuilderFormCapture
from core.web.SequenceBuilderCookieJar import SequenceBuilderCookieJar
from core.web.StandardPageFactory import StandardPageFactory
from core.web.RenderingWebView import RenderingWebView

from core.database.constants import ResponsesTable, SequencesTable, SequenceStepsTable

from core.network.SequenceBuilderNetworkAccessManager import SequenceBuilderNetworkAccessManager

class SequenceDialog(QDialog, SequenceDialog.Ui_seqBuildDialog):
    """ The sequence builder dialog """
    
    def __init__(self, framework, parent=None):
        super(SequenceDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.framework = framework

        # TODO: move to framework constants
        self.known_media_types = ('text/css', 'application/javascript', 'text/javascript', 'image/gif', 'image/png', 'image/jpeg', 'image/bmp')

        self.cookieJar = SequenceBuilderCookieJar(self.framework, self)
        self.networkAccessManager = SequenceBuilderNetworkAccessManager(self.framework, self.cookieJar)
        self.formCapture = SequenceBuilderFormCapture(self.framework, self)
        self.pageFactory = SequenceBuilderPageFactory(self.framework, self.formCapture, self)
        self.standardPageFactory = StandardPageFactory(self.framework, self.networkAccessManager, self)

        QObject.connect(self.networkAccessManager, SIGNAL('finished(QNetworkReply *)'), self.process_request_finished)
        self.embedded = EmbeddedWebkitWidget.EmbeddedWebkitWidget(self.framework, self.networkAccessManager, self.pageFactory, self.webBrowserFrame, self)

        self.sequenceTabWidget.currentChanged.connect(self.handle_currentChanged)
        self.is_recording = False
        self.sequence_items = {}
        self.qlock = QMutex()
        self.startRecordingButton.clicked.connect(self.handle_startRecording_clicked)
        self.stopRecordingButton.clicked.connect(self.handle_stopRecording_clicked)
        self.saveSequenceButton.clicked.connect(self.handle_saveSequence_clicked)
        self.deleteSequenceButton.clicked.connect(self.handle_deleteSequence_clicked)
        self.deleteSequenceButton.setEnabled(False)

        # attach RenderingWebView to renderViewSequenceTabWidget
        self.sequenceRenderView_Layout = QVBoxLayout(self.renderViewSequenceTabWidget)
        self.sequenceRenderView = RenderingWebView(self.framework, self.standardPageFactory, self.renderViewSequenceTabWidget)
        self.sequenceRenderView_Layout.addWidget(self.sequenceRenderView)
        self.sequencePropertiesTabWidget.currentChanged.connect(self.handle_properties_currentChanged)
        self.sequenceRenderView.page().selectionChanged.connect(self.handle_renderView_selectionChanged)

        # use Scintilla for request and response views
        self.sequenceRequestView_Layout = QVBoxLayout(self.requestViewSequenceTabWidget)
        self.sequenceRequestViewEdit = Qsci.QsciScintilla(self.requestViewSequenceTabWidget)
        self.setScintillaProperties(self.sequenceRequestViewEdit)
        self.sequenceRequestView_Layout.addWidget(self.sequenceRequestViewEdit)

        self.sequenceResponseView_Layout = QVBoxLayout(self.responseViewSequenceTabWidget)
        self.sequenceResponseViewEdit = Qsci.QsciScintilla(self.responseViewSequenceTabWidget)
        self.setScintillaProperties(self.sequenceResponseViewEdit, 'html')
        self.sequenceResponseView_Layout.addWidget(self.sequenceResponseViewEdit)

        self.sequenceStepsTreeWidget.itemClicked.connect(self.handle_steps_itemClicked)
        self.sequenceStepsTreeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.menu = QMenu(self.sequenceStepsTreeWidget)
        self.connect(self.sequenceStepsTreeWidget, SIGNAL("customContextMenuRequested(const QPoint&)"), self.sequence_steps_context_menu)
        action = QAction("Remove from sequence", self)
        action.triggered.connect(self.handle_remove_from_sequence)
        self.menu.addAction(action)
        action = QAction("Copy URL", self)
        action.triggered.connect(self.sequence_step_copy_url)
        self.menu.addAction(action)

        self.inSessionPatternEdit.textChanged.connect(self.handle_sessionEdit_textChanged)
        self.inSessionPatternRE.stateChanged.connect(self.handle_sessionRE_stateChanged)
        self.outOfSessionPatternEdit.textChanged.connect(self.handle_sessionEdit_textChanged)
        self.outOfSessionPatternRE.stateChanged.connect(self.handle_sessionRE_stateChanged)

        QObject.connect(self.sequencesComboBox, SIGNAL('currentIndexChanged(const QString &)'), self.handle_sequenceCombo_text_currentIndexChanged)
        QObject.connect(self.sequencesComboBox, SIGNAL('currentIndexChanged(int)'), self.handle_sequenceCombo_currentIndexChanged)

        self.useSessionDetectionCheckbox.stateChanged.connect(self.handle_useSessionDection_stateChanged)
        self.setUseSessionDetection()
        
        self.includeMediaCheckbox.stateChanged.connect(self.handle_includeMedia_stateChanged)

        self.framework.subscribe_add_sequence_builder_response_id(self.add_manual_sequence_builder_item)

        self.originatingResponses = {}
        self.sequenceResponseIds = set()

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def display_confirm_dialog(self, message):
        response = QMessageBox.question(self, 'Confirm', message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if 0 != (response & QMessageBox.Yes):
            return True
        else:
            return False

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.populate_sequence_combo()

    def db_detach(self):
        if self.Data:
            self.close_cursor()
            self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def populate_sequence_combo(self, selectedText = ''):
        self.sequencesComboBox.clear()
        item = self.sequencesComboBox.addItem('New Sequence - %s' % (time.asctime(time.localtime())), '-1')
        
        for row in self.Data.get_all_sequences(self.cursor):
            sequenceItem = [m or '' for m in row]
            name = str(sequenceItem[1])
            Id = str(sequenceItem[0])
            item = self.sequencesComboBox.addItem(name, Id)

        if selectedText:
            index = self.sequencesComboBox.findText(selectedText)
            self.sequencesComboBox.setCurrentIndex(index)
        else:
            self.populate_manual_sequence_items_from_db()

    def handle_deleteSequence_clicked(self):
        sequenceId = self.sequencesComboBox.itemData(self.sequencesComboBox.currentIndex())
        if self.display_confirm_dialog('Delete sequence: %s?' % self.sequencesComboBox.currentText()):
            self.Data.delete_sequence(self.cursor, int(sequenceId))
            
        self.populate_sequence_combo()

    def handle_sequenceCombo_text_currentIndexChanged(self, text):
        pass

    def handle_sequenceCombo_currentIndexChanged(self, index):
        if -1 == index:
            return

        sequenceId = self.sequencesComboBox.itemData(index)

        if '-1' != sequenceId:
            self.deleteSequenceButton.setEnabled(True)
        else:
            self.deleteSequenceButton.setEnabled(False)

        self.fill_sequence_info(sequenceId)

    def handle_saveSequence_clicked(self):
        try:
            currentItem = self.sequencesComboBox.itemData(self.sequencesComboBox.currentIndex())
            sequenceId = currentItem
            print(('current', sequenceId))
            if '' == sequenceId:
                return
            sequenceId = int(sequenceId)
            if -1 == sequenceId:
                sequenceId = self.Data.insert_new_sequence(self.cursor, 
                                                  [None, 
                                                   str(self.sequencesComboBox.currentText()), str(self.sequenceTypeComboBox.currentText()),
                                                   int(self.useSessionDetectionCheckbox.isChecked()), int(self.includeMediaCheckbox.isChecked()),
                                                   int(self.useBrowserCheckbox.isChecked()), 
                                                   str(self.inSessionPatternEdit.text()), int(self.inSessionPatternRE.isChecked()),
                                                   str(self.outOfSessionPatternEdit.text()), int(self.outOfSessionPatternRE.isChecked()),
                                                   int(self.dynamicDataCheckbox.isChecked())
                                                   ])
            else:
                self.Data.update_sequence(self.cursor, 
                                                  [str(self.sequencesComboBox.currentText()), str(self.sequenceTypeComboBox.currentText()),
                                                   int(self.useSessionDetectionCheckbox.isChecked()), int(self.includeMediaCheckbox.isChecked()),
                                                   int(self.useBrowserCheckbox.isChecked()), 
                                                   str(self.inSessionPatternEdit.text()), int(self.inSessionPatternRE.isChecked()),
                                                   str(self.outOfSessionPatternEdit.text()), int(self.outOfSessionPatternRE.isChecked()),
                                                   int(self.dynamicDataCheckbox.isChecked()),
                                                   sequenceId])
                self.Data.clear_sequence_steps(self.cursor, sequenceId)
                self.Data.clear_sequence_parameters(self.cursor, sequenceId)

            # insert steps
            for index in range(0, self.sequenceStepsTreeWidget.topLevelItemCount()):
                item = self.sequenceStepsTreeWidget.topLevelItem(index)
                if item:
                    stepnum  = str(item.text(0))
                    sequence_item = self.sequence_items[stepnum]
                    isEnabled = not (item.isDisabled() or item.isHidden())
                    isHidden = item.isHidden() and not item.isDisabled()
                    self.Data.insert_sequence_step(self.cursor, [sequenceId, int(stepnum), int(sequence_item['responseId']), isEnabled, isHidden])

            # insert parameters
            # TODO: populate and read from tree view
            parameters = self.formCapture.allParameters(self.sequenceResponseIds)
            print(('save parameters', parameters))
            for responseId, requestId, param, value, origin in parameters:
                if 'source' == origin:
                    if responseId:
                        self.Data.insert_sequence_source_parameter(self.cursor, [
                                sequenceId,
                                responseId,
                                param.source,
                                param.position,
                                param.Type,
                                param.name,
                                json.dumps(value).encode('utf-8'),
                                True
                                ])
                elif 'target' == origin:
                    self.Data.insert_sequence_target_parameter(self.cursor, [
                            sequenceId,
                            responseId,
                            param.source,
                            param.position,
                            param.name,
                            json.dumps(value).encode('utf-8'),
                            True
                            ])

            # insert cookies
            # TODO: populate and read from tree view
            cookieList = self.cookieJar.allCookies()
            for cookie in cookieList:
                self.Data.insert_sequence_cookie(self.cursor, [
                        sequenceId,
                        str(cookie.domain()),
                        str(cookie.name(), 'utf-8'),
                        cookie.toRawForm().data(),
                        True
                        ])

            self.Data.commit()
        except Exception as error:
            self.Data.rollback()
            self.framework.report_exception(error)
            raise

        self.framework.signal_sequences_changed()
        self.populate_sequence_combo(self.sequencesComboBox.currentText())

    def add_manual_sequence_builder_item(self, responseId):
        if not self.is_recording:
            self.populate_manual_sequence_items_from_db()

    def populate_manual_sequence_items_from_db(self):
        responseIds = self.Data.get_sequence_builder_manual_items(self.cursor).fetchall()
        if len(responseIds) == 0:
            return
        self.startRecordingButton.setEnabled(False)
        for item in responseIds:
            responseId = str(item[0])
            self.infer_source_information(responseId)
            self.append_sequence_item(responseId)
        self.Data.clear_sequence_builder_manual_items(self.cursor)

    def infer_source_information(self, responseId):
        # TODO: implement
        pass

    def fill_sequence_info(self, sequenceId):
        self.sequenceResponseIds = set()
        sequenceId = int(sequenceId)
        if -1 == sequenceId:
            sequenceItem = (sequenceId, '', '', 0, 0, 0, '', 0, '', 0, 0)
        else:
            row = self.Data.get_sequence_by_id(self.cursor, sequenceId)
            if not row:
                return
            datarow = list(row)
            sequenceItem = [m or '' for m in datarow]

        self.reset_sequence_layout(sequenceId, sequenceItem)

    def reset_sequence_layout(self, sequenceId, sequenceItem):

        index = self.sequenceTypeComboBox.findText(str(sequenceItem[2]))
        if -1 != index:
            self.sequenceTypeComboBox.setCurrentIndex(index)
        else:
            self.sequenceTypeComboBox.setCurrentIndex(0)

        self.useSessionDetectionCheckbox.setChecked(bool(sequenceItem[3]))
        self.includeMediaCheckbox.setChecked(bool(bool(sequenceItem[4])))
        self.useBrowserCheckbox.setChecked(bool(sequenceItem[5]))
        self.inSessionPatternEdit.setText(str(sequenceItem[6]))
        self.inSessionPatternRE.setChecked(bool(sequenceItem[7]))
        self.outOfSessionPatternEdit.setText(str(sequenceItem[8]))
        self.outOfSessionPatternRE.setChecked(bool(sequenceItem[9]))
        self.dynamicDataCheckbox.setChecked(bool(sequenceItem[SequencesTable.DYNAMIC_DATA]))

        self.sequencePropertiesTabWidget.setCurrentIndex(0)
        self.sequenceResponseViewEdit.setText('')
        self.sequenceRequestViewEdit.setText('')
        self.sequenceRenderView.setHtml('', QUrl('about:blank'))

        self.sequenceStepsTreeWidget.clear()
        self.sequence_items = {}

        if -1 != sequenceId:
            sequenceSteps = []
            for row in self.Data.get_sequence_steps(self.cursor, sequenceId):
                stepItems = [m or '' for m in row]
                sequenceSteps.append(stepItems)
            for stepItems in sequenceSteps:
                item = self.append_sequence_item(str(stepItems[SequenceStepsTable.RESPONSE_ID]))
                if not bool(stepItems[SequenceStepsTable.IS_ENABLED]):
                    item.setHidden(True)
                    if not bool(stepItems[SequenceStepsTable.IS_HIDDEN]):
                        item.setDisabled(True)

        self.is_recording = False
        self.stopRecordingButton.setEnabled(False)
        self.startRecordingButton.setEnabled(True)

        self.setUseSessionDetection()
        self.run_pattern_matches()

    def handle_useSessionDection_stateChanged(self, state):
        self.setUseSessionDetection()

    def handle_includeMedia_stateChanged(self):
        for index in range(0, self.sequenceStepsTreeWidget.topLevelItemCount()):
            item = self.sequenceStepsTreeWidget.topLevelItem(index)
            if item and not item.isDisabled():
                contentType = str(item.text(3))
                self.hide_media_type_item(item, contentType)

    def setUseSessionDetection(self):
        self.inSessionPatternEdit.setEnabled(self.useSessionDetectionCheckbox.isChecked())
        self.inSessionPatternRE.setEnabled(self.useSessionDetectionCheckbox.isChecked())
        self.outOfSessionPatternEdit.setEnabled(self.useSessionDetectionCheckbox.isChecked())
        self.outOfSessionPatternRE.setEnabled(self.useSessionDetectionCheckbox.isChecked())
        if not self.useSessionDetectionCheckbox.isChecked():
            self.inSessionPatternEdit.setPalette(QApplication.palette())
            self.outOfSessionPatternEdit.setPalette(QApplication.palette())

    # TODO: refactor this code - 
    def setScintillaProperties(self, scintillaWidget, lexerType = ''):
        scintillaWidget.setFont(self.framework.get_font())
        scintillaWidget.setWrapMode(1)
        scintillaWidget.zoomTo(self.framework.get_zoom_size())
        # TOOD: set based on line numbers (size is in pixels)
        scintillaWidget.setMarginWidth(1, '1000')
        self.framework.subscribe_zoom_in(lambda: scintillaWidget.zoomIn())
        self.framework.subscribe_zoom_out(lambda: scintillaWidget.zoomOut())
        if 'html' == lexerType:
            lexerInstance = Qsci.QsciLexerHTML(scintillaWidget)
            lexerInstance.setFont(self.framework.get_font())
            scintillaWidget.setLexer(lexerInstance)

    def handle_startRecording_clicked(self):
        self.sequenceStepsTreeWidget.clear()
        self.stopRecordingButton.setEnabled(True)
        self.startRecordingButton.setEnabled(False)
        self.cookieJar.start_tracking()
        self.formCapture.start_tracking()
        self.sequence_items = {}
        self.sequenceResponseIds = set()
        self.is_recording = True
        self.sequenceTabWidget.setCurrentIndex(1)

    def handle_stopRecording_clicked(self):
        self.is_recording = False
        self.cookieJar.stop_tracking()
        self.formCapture.stop_tracking()
        self.stopRecordingButton.setEnabled(False)
        self.startRecordingButton.setEnabled(True)

    def handle_currentChanged(self, index):
        # TODO: clean this up
        if 3 == index:
            self.sequenceParametersTreeWidget.clear()
            print(('sequenceResponseIds', type(self.sequenceResponseIds), self.sequenceResponseIds))
            parameters = self.formCapture.allParameters(self.sequenceResponseIds)
            for responseId, requestId, param, value, origin in parameters:
                print((responseId, requestId, param, value, origin))
                rId = ''
                Xref = ''
                source = ''
                target = ''
                value_type = param.Type
                position = str(param.position)
                if 'source' == origin:
#                    rId = requestId
#                    Xref = self.formCapture.get_sequence_transition(requestId)
                    rId = responseId
                    Xref = requestId
                    source = param.source
                elif 'target' == origin:
                    rId = responseId
                    Xref = requestId
                    target = param.source

                item = QTreeWidgetItem([
                        '',  
                        rId,
                        Xref,
                        source,
                        value_type,
                        position,
                        target,
                        param.name,
                        ','.join(value), # value can be list
                        param.url,
                        ])
                self.sequenceParametersTreeWidget.addTopLevelItem(item)
        elif 2 == index:
            self.sequenceCookiesTreeWidget.clear()
            cookieList = self.cookieJar.allCookies()
            for cookie in cookieList:
                item = QTreeWidgetItem([
                        '',  
                        str(cookie.domain()),
                        str(cookie.name()),
                        str(cookie.value()),
                        str(cookie.path()),
                        str(cookie.expirationDate().toUTC().toString('MM/dd/yyyy hh:mm:ss')),
                        str(cookie.isSessionCookie()),
                        str(cookie.isHttpOnly()),
                        str(cookie.isSecure()),
                        ])
                if self.cookieJar.is_cookie_tracked(str(cookie.domain()), str(cookie.name())):
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)
                self.sequenceCookiesTreeWidget.addTopLevelItem(item)

    def process_request_finished(self, reply):
        if not self.is_recording:
            return
        self.qlock.lock()
        try:
            responseId, requestId, xrefId = '', '', ''
            varId = reply.attribute(QNetworkRequest.User)
            if varId is not None:
                responseId = str(varId)
            varId = reply.attribute(QNetworkRequest.User + 1)
            if varId is not None:
                requestId = str(varId)
            varId = reply.attribute(QNetworkRequest.User + 2)
            if varId is not None:
                xrefId = str(varId)

            print(('process_request_finished', responseId, requestId, xrefId))

            if xrefId and requestId and responseId:
                if requestId not in self.originatingResponses:
                    self.originatingResponses[requestId] = responseId

                # TODO: is this necessary?
                originatingObject = reply.request().originatingObject()
                if originatingObject:
                    originatingObject.setProperty('RAFT_responseId', self.originatingResponses[requestId])

#            print(self.originatingResponses)

            if responseId:
                self.append_sequence_item(responseId, requestId)
        finally:
            self.qlock.unlock()

    def append_sequence_item(self, responseId, requestId = ''):
        topItem = self.sequenceStepsTreeWidget.topLevelItem(self.sequenceStepsTreeWidget.topLevelItemCount()-1)
        if topItem is None:
            current_max = 0
        else:
            current_max = int(topItem.text(0))
        stepnum = str(current_max + 1)

        row = self.Data.read_responses_by_id(self.cursor, responseId)
        if not row:
            return

        self.sequenceResponseIds.add(responseId)

        responseItems = interface.data_row_to_response_items(row)

        url = responseItems[ResponsesTable.URL]
        method = responseItems[ResponsesTable.REQ_METHOD]
        contentType = responseItems[ResponsesTable.RES_CONTENT_TYPE].lower().strip()
        charset = ContentHelper.getCharSet(contentType)
        if contentType and ';' in contentType:
            contentType = contentType[0:contentType.index(';')]

        reqHeaders = responseItems[ResponsesTable.REQ_HEADERS]
        reqData = responseItems[ResponsesTable.REQ_DATA]
        requestHeaders, requestBody, rawRequest = ContentHelper.combineRaw(reqHeaders, reqData)

        resHeaders = responseItems[ResponsesTable.RES_HEADERS]
        resData = responseItems[ResponsesTable.RES_DATA]
        responseHeaders, responseBody, rawResponse = ContentHelper.combineRaw(resHeaders, resData, charset)

        sequence_item = {
            'responseUrl' : url,
            'responseId' : responseId,
            'rawResponse' : rawResponse,
            'rawRequest' : rawRequest,
            'method' : method,
            }

        self.sequence_items[stepnum] = sequence_item
        status = self.check_pattern_match(sequence_item)
        item = QTreeWidgetItem([stepnum, status, method, contentType, url])
        self.sequenceStepsTreeWidget.addTopLevelItem(item)

        self.hide_media_type_item(item, contentType)

        self.formCapture.process_target_request(responseId, requestId, method, url, reqHeaders, reqData)

        return item

    def hide_media_type_item(self, item, contentType):
        # TODO: move this to a common module that applies mime type checking
        hide_it = not self.includeMediaCheckbox.isChecked()
        if 'html' in contentType:
            pass
        elif contentType in self.known_media_types:
            item.setHidden(hide_it)
        elif '/' in contentType:
            ctype, stype = contentType.split('/', 1)
            if ctype in ('audio', 'image', 'video'):
                item.setHidden(hide_it)

    def handle_properties_currentChanged(self, index):
        item = self.sequenceStepsTreeWidget.currentItem()
        if item is None:
            return

        self.inSessionPatternEdit.setPalette(QApplication.palette())
        self.outOfSessionPatternEdit.setPalette(QApplication.palette())

        if 0 == index:
            pass
        elif 1 == index:
           self.update_sequenceRequestView(str(item.text(0)))
        elif 2 == index:
            self.update_sequenceResponseView(str(item.text(0)))
        elif 3 == index:
            self.update_sequenceRenderView(str(item.text(0)))

    def handle_renderView_selectionChanged(self):
        pass

    def handle_steps_itemClicked(self, item, column):

        index = self.sequencePropertiesTabWidget.currentIndex()

        if 0 == index:
            return

        if item is None:
            return

        if 1 == index:
           self.update_sequenceRequestView(str(item.text(0)))
        elif 2 == index:
            self.update_sequenceResponseView(str(item.text(0)))
        elif 3 == index:
            self.update_sequenceRenderView(str(item.text(0)))

    def update_sequenceRenderView(self, stepnum):
        sequence_item = self.sequence_items[stepnum]
        self.sequenceRenderView.fill_from_db(sequence_item['responseId'], sequence_item['responseUrl'])

    def update_sequenceResponseView(self, stepnum):
        sequence_item = self.sequence_items[stepnum]
        rawResponse = sequence_item['rawResponse']
        self.sequenceResponseViewEdit.setText(rawResponse)
        self.run_pattern_matches()

    def update_sequenceRequestView(self, stepnum):
        sequence_item = self.sequence_items[stepnum]
        rawRequest = sequence_item['rawRequest']
        self.sequenceRequestViewEdit.setText(rawRequest)
        self.run_pattern_matches()

    def check_pattern_match(self, sequence_item):
        if not self.useSessionDetectionCheckbox.isChecked():
            return ''

        rawResponse = sequence_item['rawResponse']
        is_insession = False
        is_outofsession = False

        searchText = str(self.inSessionPatternEdit.text())
        if searchText:
            if self.inSessionPatternRE.isChecked():
                try:
                    if self.re_insession is None:
                        self.re_insession = re.compile(searchText, re.I)
                    if self.re_insession.search(rawResponse):
                        is_insession = True
                except Exception as e:
                    self.framework.report_implementation_error(e)
            else:
                if -1 != rawResponse.lower().find(searchText.lower()):
                    is_insession = True

        searchText = str(self.outOfSessionPatternEdit.text())
        if searchText:
            if self.outOfSessionPatternRE.isChecked():
                try:
                    if self.re_outofsession is None:
                        self.re_outofsession = re.compile(searchText, re.I)
                    if self.re_outofsession.search(rawResponse):
                        is_outofsession = True
                except Exception as e:
                    self.framework.report_implementation_error(e)

            else:
                if -1 != rawResponse.lower().find(searchText.lower()):
                    is_outofsession = True

        if is_insession and not is_outofsession:
            return 'In-Session'
        elif not is_insession and is_outofsession:
            return 'Out-of-Session'
        elif not is_insession and not is_outofsession:
            return ''
        else:
            return 'Conflict'

    def run_pattern_matches(self):
        if not self.useSessionDetectionCheckbox.isChecked():
            # no pattern matching
            for index in range(0, self.sequenceStepsTreeWidget.topLevelItemCount()):
                item = self.sequenceStepsTreeWidget.topLevelItem(index)
                if item:
                    item.setText(1, '')
            return
        else:
            self.do_apply_pattern_selection(self.inSessionPatternEdit, self.inSessionPatternRE)
            self.do_apply_pattern_selection(self.outOfSessionPatternEdit, self.outOfSessionPatternRE)

            for index in range(0, self.sequenceStepsTreeWidget.topLevelItemCount()):
                item = self.sequenceStepsTreeWidget.topLevelItem(index)
                if item:
                    step_num = str(item.text(0))
                    sequence_item = self.sequence_items[step_num]
                    status = self.check_pattern_match(sequence_item)
                    item.setText(1, status)

    def handle_sessionEdit_textChanged(self, text):
        self.re_insession = None
        self.re_outofsession = None
        self.run_pattern_matches()

    def handle_sessionRE_stateChanged(self, state):
        self.re_insession = None
        self.re_outofsession = None
        self.run_pattern_matches()

    def do_apply_pattern_selection(self, search_line_edit, re_checkbox):
        searchText = search_line_edit.text()
        is_re = re_checkbox.isChecked()

        if not searchText:
            search_line_edit.setPalette(QApplication.palette())
            return

        tabindex = self.sequencePropertiesTabWidget.currentIndex()

        if 0 == tabindex:
            return
        elif 1 == tabindex:
            pass
        elif 2 == tabindex:
            # Scintilla doesn't understand same regex characters as Python
            # TODO: consider improving this emulation
            if is_re:
                try:
                    r = re.compile(str(searchText), re.I)
                    tmp = str(self.sequenceResponseViewEdit.text())
                    m = r.search(tmp)
                    if m:
                        searchText = m.group(0)
                        is_re = False
                except Exception as e:
                    pass
                      
            if not self.sequenceResponseViewEdit.findFirst(searchText, is_re, False, False, True, True, 0, 0):
                p = search_line_edit.palette()
                p.setColor(QPalette.Text, QColor('red'))
                search_line_edit.setPalette(p)
            else:
                search_line_edit.setPalette(QApplication.palette())
        elif 3 == tabindex:
            pass

    def sequence_steps_context_menu(self, point):
        self.menu.exec_(self.sequenceStepsTreeWidget.mapToGlobal(point))

    def handle_remove_from_sequence(self):
        item = self.sequenceStepsTreeWidget.currentItem()
        if item is None:
            return
        item.setDisabled(True)
        item.setHidden(True)

    def sequence_step_copy_url(self):
        item = self.sequenceStepsTreeWidget.currentItem()
        if item is None:
            return
        curUrl = item.text(4)
        if curUrl:
            QApplication.clipboard().setText(curUrl)

