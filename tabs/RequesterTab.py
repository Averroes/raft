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
from PyQt4.QtCore import Qt, QObject, SIGNAL, QUrl
from PyQt4.QtGui import *
from PyQt4 import Qsci


from io import StringIO
from urllib import parse as urlparse
import uuid
import re

from actions import interface

from dialogs.RequestResponseDetailDialog import RequestResponseDetailDialog

from core.database.constants import ResponsesTable
from core.fuzzer.RequestRunner import RequestRunner
from core.data import ResponsesDataModel
from widgets.ResponsesContextMenuWidget import ResponsesContextMenuWidget
from widgets.MiniResponseRenderWidget import MiniResponseRenderWidget
from widgets.RequestResponseWidget import RequestResponseWidget
from core.network.InMemoryCookieJar import InMemoryCookieJar

class RequesterTab(QObject):
    def __init__(self, framework, mainWindow):
        QObject.__init__(self, mainWindow)
        self.framework = framework
        self.mainWindow = mainWindow

        self.mainWindow.requesterSendButton.clicked.connect(self.requester_send_button_clicked)
        self.mainWindow.bulkRequestPushButton.clicked.connect(self.requester_bulk_request_button_clicked)
        self.mainWindow.requesterHistoryClearButton.clicked.connect(self.requester_history_clear_button_clicked)
        self.mainWindow.reqTabWidget.currentChanged.connect(self.handle_tab_currentChanged)
        self.mainWindow.requesterSequenceCheckBox.stateChanged.connect(self.handle_requesterSequenceCheckBox_stateChanged)
        self.mainWindow.bulkRequestSequenceCheckBox.stateChanged.connect(self.handle_bulkRequestSequenceCheckBox_stateChanged)
        self.mainWindow.sequenceRunnerRunButton.clicked.connect(self.handle_sequenceRunnerRunButton_clicked)
        self.pending_request = None
        self.pending_bulk_requests = None
        self.pending_sequence_requests = None

        self.re_request = re.compile(r'^(\S+)\s+((?:https?://(?:\S+\.)+\w+(?::\d+)?)?/.*)\s+HTTP/\d+\.\d+\s*$', re.I)
        self.re_request_cookie = re.compile(r'^Cookie:\s*(\S+)', re.I|re.M)
        self.re_replacement = re.compile(r'\$\{(\w+)\}')

        self.framework.subscribe_populate_requester_response_id(self.requester_populate_response_id)
        self.framework.subscribe_populate_bulk_requester_responses(self.bulk_requester_populate_responses)
        self.framework.subscribe_sequences_changed(self.fill_sequences)

        self.setup_requester_tab()

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.fill_requesters()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def setup_requester_tab(self):

        self.historyRequestResponse = RequestResponseWidget(self.framework, self.mainWindow.requesterHistoryTabWidget, self.mainWindow.requesterHistorySearchResultsPlaceholder, self)
        self.requesterHistoryDataModel = ResponsesDataModel.ResponsesDataModel(self.framework, self)
        self.mainWindow.requesterHistoryTreeView.setModel(self.requesterHistoryDataModel)
        self.mainWindow.requesterHistoryTreeView.activated.connect(self.fill_history_request_response)
        self.mainWindow.requesterHistoryTreeView.clicked.connect(self.fill_history_request_response)
        self.mainWindow.requesterHistoryTreeView.doubleClicked.connect(self.requester_history_item_double_clicked)
        self.historyResponsesContextMenu = ResponsesContextMenuWidget(self.framework, self.requesterHistoryDataModel, self.mainWindow.requesterHistoryTreeView, self)
        self.historyResponsesContextMenu.set_currentChanged_callback(self.fill_history_request_response)

        self.sequenceRunnerRequestResponse = RequestResponseWidget(self.framework, self.mainWindow.sequenceRunnerTabWidget, self.mainWindow.sequenceRunnerSearchResultsPlaceholder, self)
        self.sequenceRunnerDataModel = ResponsesDataModel.ResponsesDataModel(self.framework, self)
        self.mainWindow.sequenceRunnerTreeView.setModel(self.sequenceRunnerDataModel)
        self.mainWindow.sequenceRunnerTreeView.activated.connect(self.fill_sequence_runner_request_response)
        self.mainWindow.sequenceRunnerTreeView.clicked.connect(self.fill_sequence_runner_request_response)
        self.mainWindow.sequenceRunnerTreeView.doubleClicked.connect(self.requester_sequence_runner_item_double_clicked)
        self.sequence_runnerResponsesContextMenu = ResponsesContextMenuWidget(self.framework, self.sequenceRunnerDataModel, self.mainWindow.sequenceRunnerTreeView, self)
        self.sequence_runnerResponsesContextMenu.set_currentChanged_callback(self.fill_sequence_runner_request_response)

        self.miniResponseRenderWidget = MiniResponseRenderWidget(self.framework, self.mainWindow.reqRespTabWidget, True, self)

        self.scopeController = self.framework.getScopeController()

    def requester_history_item_double_clicked(self, index):
        Id = interface.index_to_id(self.requesterHistoryDataModel, index)
        if Id:
            dialog = RequestResponseDetailDialog(self.framework, Id, self.mainWindow)
            dialog.show()
            dialog.exec_()

    def fill_history_request_response(self, index):
        Id = interface.index_to_id(self.requesterHistoryDataModel, index)
        if Id:
            self.historyRequestResponse.fill(Id)

    def requester_sequence_runner_item_double_clicked(self, index):
        Id = interface.index_to_id(self.sequenceRunnerDataModel, index)
        if Id:
            dialog = RequestResponseDetailDialog(self.framework, Id, self.mainWindow)
            dialog.show()
            dialog.exec_()

    def fill_sequence_runner_request_response(self, index):
        Id = interface.index_to_id(self.sequenceRunnerDataModel, index)
        if Id:
            self.sequenceRunnerRequestResponse.fill(Id)

    def fill_requesters(self):
        # requesters
        self.requesterHistoryDataModel.clearModel()
        history_items = []
        for row in self.Data.get_all_requester_history(self.cursor):
            response_item = interface.data_row_to_response_items(row)
            history_items.append(response_item)
        self.requesterHistoryDataModel.append_data(history_items)

        self.fill_sequences()

        self.mainWindow.requesterUrlEdit.setText(self.framework.get_raft_config_value('requesterUrlEdit'))
        self.mainWindow.bulkRequestUrlListEdit.setPlainText(self.framework.get_raft_config_value('bulkRequestUrlListEdit'))

    def fill_sequences(self):
        self.fill_sequences_combo_box(self.mainWindow.requesterSequenceComboBox)
        self.fill_sequences_combo_box(self.mainWindow.bulkRequestSequenceComboBox)
        self.fill_sequences_combo_box(self.mainWindow.sequenceRunnerSequenceComboBox)

    def requester_populate_response_id(self, Id):
        row = self.Data.read_responses_by_id(self.cursor, Id)
        if not row:
            return

        responseItems = interface.data_row_to_response_items(row)

        method, url, template_text = self.generate_template_for_response_item(responseItems)

        self.set_combo_box_text(self.mainWindow.requesterRequestMethod, method.upper())
        self.mainWindow.requesterUrlEdit.setText(url)
        self.mainWindow.requesterTemplateEdit.setPlainText(template_text)

    def bulk_requester_populate_responses(self, id_list):

        url_list = []
        first = True
        for Id in id_list:
            row = self.Data.read_responses_by_id(self.cursor, Id)
            if not row:
                continue

            responseItems = interface.data_row_to_response_items(row)
            url = responseItems[ResponsesTable.URL]
            if url not in url_list:
                url_list.append(url)

            if first:
                method, url, template_text = self.generate_template_for_response_item(responseItems)
                self.set_combo_box_text(self.mainWindow.bulkRequestMethodEdit, method.upper())
                self.mainWindow.bulkRequestTemplateEdit.setPlainText(template_text)
                first = False

        self.mainWindow.bulkRequestUrlListEdit.setPlainText('\n'.join(url_list))

    def generate_template_for_response_item(self, responseItems):
        url = responseItems[ResponsesTable.URL]
        reqHeaders = str(responseItems[ResponsesTable.REQ_HEADERS], 'utf-8', 'ignore')
        reqData = str(responseItems[ResponsesTable.REQ_DATA], 'utf-8', 'ignore')
        method = responseItems[ResponsesTable.REQ_METHOD]
        splitted = urlparse.urlsplit(url)

        useragent = self.framework.useragent()
        has_cookie = False
        template = StringIO()
        template.write('${method} ${request_uri} HTTP/1.1\n')
        first = True
        for line in reqHeaders.splitlines():
            if not line:
                break
            if first and self.re_request.match(line):
                first = False
                continue
            if ':' in line:
                name, value = [v.strip() for v in line.split(':', 1)]
                lname = name.lower()
                if 'host' == lname:
                    if splitted.hostname and value == splitted.hostname:
                        template.write('Host: ${host}\n')
                        continue
                elif 'user-agent' == lname:
                    if useragent == value:
                        template.write('User-Agent: ${user_agent}\n')
                        continue
            template.write(line)
            template.write('\n')
        template.write('\n')
        template.write(reqData)

        return method, url, template.getvalue()

    def set_combo_box_text(self, comboBox, selectedText):
        index = comboBox.findText(selectedText)
        if -1 == index:
            comboBox.addItem(selectedText)
            index = comboBox.findText(selectedText)
        comboBox.setCurrentIndex(index)

    def handle_requesterSequenceCheckBox_stateChanged(self, state):
        self.mainWindow.requesterSequenceComboBox.setEnabled(self.mainWindow.requesterSequenceCheckBox.isChecked())

    def handle_bulkRequestSequenceCheckBox_stateChanged(self, state):
        self.mainWindow.bulkRequestSequenceComboBox.setEnabled(self.mainWindow.bulkRequestSequenceCheckBox.isChecked())

    def handle_tab_currentChanged(self, index):
        # TODO: must this hard-coded ?
        if 0 == index:
            self.fill_sequences_combo_box(self.mainWindow.requesterSequenceComboBox)
        elif 1 == index:
            self.fill_sequences_combo_box(self.mainWindow.bulkRequestSequenceComboBox)
        elif 2 == index:
            self.fill_sequences_combo_box(self.mainWindow.sequenceRunnerSequenceComboBox)

    def requester_send_button_clicked(self):
        """ Make a request from the Request tab """

        if 'Cancel' == self.mainWindow.requesterSendButton.text() and self.pending_request is not None:
            self.pending_request.cancel()
            self.pending_request = None
            self.mainWindow.requesterSendButton.setText('Send')
            return

        qurl = QUrl.fromUserInput(self.mainWindow.requesterUrlEdit.text())
        url = qurl.toEncoded().data().decode('utf-8')
        self.mainWindow.requesterUrlEdit.setText(url)

        self.framework.set_raft_config_value('requesterUrlEdit', url)
        templateText = str(self.mainWindow.requesterTemplateEdit.toPlainText())
        method = str(self.mainWindow.requesterRequestMethod.currentText())

        use_global_cookie_jar = self.mainWindow.requesterUseGlobalCookieJar.isChecked()
        replacements = self.build_replacements(method, url)
        (method, url, headers, body) = self.process_template(url, templateText, replacements)

        sequenceId = None
        if self.mainWindow.requesterSequenceCheckBox.isChecked():
            sequenceId = str(self.mainWindow.requesterSequenceComboBox.itemData(self.mainWindow.requesterSequenceComboBox.currentIndex()))
        self.requestRunner = RequestRunner(self.framework, self)
        if use_global_cookie_jar:
            self.requesterCookieJar = self.framework.get_global_cookie_jar()
        else:
            self.requesterCookieJar = InMemoryCookieJar(self.framework, self)
            
        self.requestRunner.setup(self.requester_response_received, self.requesterCookieJar, sequenceId)

        self.pending_request = self.requestRunner.queue_request(method, url, headers, body)
        self.mainWindow.requesterSendButton.setText('Cancel')
        self.miniResponseRenderWidget.clear_response_render()

    def requester_response_received(self, response_id, context):
        if 0 != response_id:
            row = self.Data.read_responses_by_id(self.cursor, response_id)
            if row:
                response_item = interface.data_row_to_response_items(row)
                self.Data.insert_requester_history(self.cursor, response_id)
                self.requesterHistoryDataModel.append_data([response_item])

                url = response_item[ResponsesTable.URL]
                req_headers = response_item[ResponsesTable.REQ_HEADERS]
                req_body = response_item[ResponsesTable.REQ_DATA]
                res_headers = response_item[ResponsesTable.RES_HEADERS]
                res_body = response_item[ResponsesTable.RES_DATA]
                res_content_type = response_item[ResponsesTable.RES_CONTENT_TYPE]

                self.miniResponseRenderWidget.populate_response_content(url, req_headers, req_body, res_headers, res_body, res_content_type)

        self.mainWindow.requesterSendButton.setText('Send')
        self.pending_request = None

    def requester_bulk_request_button_clicked(self):
        if 'Cancel' == self.mainWindow.bulkRequestPushButton.text() and self.pending_bulk_requests is not None:
            self.cancel_bulk_requests = True
            for context, pending_request in self.pending_bulk_requests.items():
                pending_request.cancel()
            self.pending_bulk_requests = None
            self.mainWindow.bulkRequestPushButton.setText('Send')
            self.mainWindow.bulkRequestProgressBar.setValue(0)
            return

        if self.pending_bulk_requests is None:
            self.pending_bulk_requests = {}

        method = str(self.mainWindow.bulkRequestMethodEdit.currentText())
        templateText = str(self.mainWindow.bulkRequestTemplateEdit.toPlainText())

        template_url = str(self.mainWindow.bulkRequestUrlEdit.text())

        url_list = str(self.mainWindow.bulkRequestUrlListEdit.toPlainText())
        self.framework.set_raft_config_value('bulkRequestUrlListEdit', url_list)
        request_urls = url_list.splitlines()
        self.mainWindow.bulkRequestProgressBar.setValue(0)
        self.mainWindow.bulkRequestProgressBar.setMaximum(len(request_urls))

        sequenceId = None
        if self.mainWindow.bulkRequestSequenceCheckBox.isChecked():
            sequenceId = str(self.mainWindow.bulkRequestSequenceComboBox.itemData(self.mainWindow.bulkRequestSequenceComboBox.currentIndex()))

        first = True
        self.cancel_bulk_requests = False
        for request_url in request_urls:
            if self.cancel_bulk_requests:
                break
            request_url = request_url.strip()
            if request_url:
                context = uuid.uuid4().hex
                # TODO: move this hack 
                if '$' in template_url:
                    replacements = self.build_replacements(method, request_url)
                    url = self.re_replacement.sub(lambda m: replacements.get(m.group(1)), template_url)
                else:
                    url = request_url

                if not self.scopeController.isUrlInScope(url, url):
                    self.framework.log_warning('skipping out of scope URL: %s' % (url))
                    self.mainWindow.bulkRequestProgressBar.setValue(self.mainWindow.bulkRequestProgressBar.value()+1)
                    continue
                
                use_global_cookie_jar = self.mainWindow.bulkRequestUseGlobalCookieJar.isChecked()
                replacements = self.build_replacements(method, url)
                (method, url, headers, body) = self.process_template(url, templateText, replacements)

                if first:
                    self.mainWindow.bulkRequestPushButton.setText('Cancel')
                    if use_global_cookie_jar:
                        self.bulkRequesterCookieJar = self.framework.get_global_cookie_jar()
                    else:
                        self.bulkRequesterCookieJar = InMemoryCookieJar(self.framework, self)
                    self.bulk_requestRunner = RequestRunner(self.framework, self)
                    self.bulk_requestRunner.setup(self.requester_bulk_response_received, self.bulkRequesterCookieJar, sequenceId)
                    first = False

                self.pending_bulk_requests[context] = self.bulk_requestRunner.queue_request(method, url, headers, body, context)

    def requester_bulk_response_received(self, response_id, context):
        self.mainWindow.bulkRequestProgressBar.setValue(self.mainWindow.bulkRequestProgressBar.value()+1)
        context = str(context)
        if self.pending_bulk_requests is not None:
            try:
                self.pending_bulk_requests.pop(context)
            except KeyError as e:
                pass
        if 0 != response_id:
            row = self.Data.read_responses_by_id(self.cursor, response_id)
            if row:
                response_item = interface.data_row_to_response_items(row)
                self.Data.insert_requester_history(self.cursor, response_id)
                self.requesterHistoryDataModel.append_data([response_item])

        finished = False
        if self.pending_bulk_requests is None or len(self.pending_bulk_requests) == 0:
            self.mainWindow.bulkRequestProgressBar.setValue(self.mainWindow.bulkRequestProgressBar.maximum())
            finished = True
        elif self.mainWindow.bulkRequestProgressBar.value() == self.mainWindow.bulkRequestProgressBar.maximum():
            finished = True
        if finished:
            self.mainWindow.bulkRequestPushButton.setText('Send')

    def handle_sequenceRunnerRunButton_clicked(self):
        """ Run a sequence """
        if 'Cancel' == self.mainWindow.sequenceRunnerRunButton.text() and self.pending_sequence_requests is not None:
            self.cancel_sequence_requests = True
            for context, pending_request in self.pending_sequence_requests.items():
                pending_request.cancel()
            self.pending_sequence_requests = None
            self.mainWindow.sequenceRunnerButton.setText('Send')
            self.mainWindow.sequenceRunnerButton.setValue(0)
            return

        self.sequenceRunnerDataModel.clearModel()

        sequenceId = str(self.mainWindow.sequenceRunnerSequenceComboBox.itemData(self.mainWindow.sequenceRunnerSequenceComboBox.currentIndex()))
        use_global_cookie_jar = self.mainWindow.sequenceRunnerUseGlobalCookieJar.isChecked()
        if use_global_cookie_jar:
            self.sequenceRunnerCookieJar = self.framework.get_global_cookie_jar()
        else:
            self.sequenceRunnerCookieJar = InMemoryCookieJar(self.framework, self)

        self.sequence_requestRunner = RequestRunner(self.framework, self)
        self.sequence_requestRunner.setup(self.sequence_runner_response_received, self.sequenceRunnerCookieJar, sequenceId)
        self.pending_sequence_requests = self.sequence_requestRunner.run_sequence()
        self.mainWindow.sequenceRunnerRunButton.setText('Cancel')

    def sequence_runner_response_received(self, response_id, context):
        context = str(context)
        if self.pending_sequence_requests is not None:
            try:
                self.pending_sequence_requests.pop(context)
            except KeyError as e:
                print((e))
                pass

        if 0 != response_id:
            row = self.Data.read_responses_by_id(self.cursor, response_id)
            if row:
                response_item = interface.data_row_to_response_items(row)
                self.sequenceRunnerDataModel.append_data([response_item])

        if self.pending_sequence_requests is None or len(self.pending_sequence_requests) == 0:
            self.mainWindow.sequenceRunnerRunButton.setText('Send')

    def requester_history_clear_button_clicked(self):
        self.Data.clear_requester_history(self.cursor)
        self.requesterHistoryDataModel.clearModel()

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

    def build_replacements(self, method, url):
        replacements = {}
        splitted = urlparse.urlsplit(url)
        replacements['method'] = method.upper()
        replacements['url'] = url
        replacements['scheme'] = splitted.scheme or ''
        replacements['netloc'] = splitted.netloc or ''
        replacements['host'] = splitted.hostname or ''
        replacements['path'] = splitted.path or '/'
        replacements['query'] = splitted.query or ''
        replacements['fragment'] = splitted.fragment or ''
        replacements['request_uri'] = urlparse.urlunsplit(('', '', replacements['path'], replacements['query'], ''))
        replacements['user_agent'] = self.framework.useragent()
        return replacements

    def process_template(self, url, template, replacements):

        method, uri = '' ,''
        headers, body = '', ''

        # TODO: this allows for missing entries -- is this good?
        func = lambda m: replacements.get(m.group(1))

        prev = 0
        while True:
            n = template.find('\n', prev)
            if -1 == n:
                break
            if n > 0 and '\r' == template[n-1]:
                line = template[prev:n-1]
            else:
                line = template[prev:n]

            if 0 == len(line):
                # end of headers
                headers = template[0:n+1]
                body = template[n+1:]
                break
            prev = n + 1

        if not headers:
            headers = template
            body = ''
            
        # TODO: could work from ordered dict to main order?
        headers_dict = {}
        first = True
        for line in headers.splitlines():
            if not line:
                break
            if '$' in line:
                line = self.re_replacement.sub(func, line)
            if first:
                m = self.re_request.match(line)
                if not m:
                    raise Exception('Invalid HTTP request: failed to match request line: %s' % (line))
                method = m.group(1)
                uri = m.group(2)
                first = False
                continue

            if ':' in line:
                name, value = [v.strip() for v in line.split(':', 1)]
                headers_dict[name] = value
        
        if '$' in body:
            body = self.re_replacement.sub(func, body)

        url = urlparse.urljoin(url, uri)

        return (method, url, headers_dict, body)

