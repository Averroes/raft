#
# Author: Nathan Hamiel
#         Gregory Fleischer (gfleischer@gmail.com)
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


from cStringIO import StringIO
from urllib2 import urlparse
import uuid
import re
import json

from actions import interface

from dialogs.RequestResponseDetailDialog import RequestResponseDetailDialog

from core.database.constants import ResponsesTable

from core.fuzzer.RequestRunner import RequestRunner
from core.data import ResponsesDataModel
from core.web.StandardPageFactory import StandardPageFactory
from core.web.RenderingWebView import RenderingWebView
from widgets.ResponsesContextMenuWidget import ResponsesContextMenuWidget
from widgets.MiniResponseRenderWidget import MiniResponseRenderWidget
from core.network.InMemoryCookieJar import InMemoryCookieJar
from core.fuzzer import Payloads

class WebFuzzerTab(QObject):
    def __init__(self, framework, mainWindow):
        QObject.__init__(self, mainWindow)
        self.framework = framework
        self.mainWindow = mainWindow
        
        self.mainWindow.wfStdPreChk.stateChanged.connect(self.handle_wfStdPreChk_stateChanged)
        self.mainWindow.wfStdPostChk.stateChanged.connect(self.handle_wfStdPostChk_stateChanged)
        self.mainWindow.wfTempSeqChk.stateChanged.connect(self.handle_wfTempSeqChk_stateChanged)
        
        # Handle the toggling of payload mappings in the config tab
        self.mainWindow.wfPay1FuzzRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay1StaticRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay2FuzzRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay2StaticRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay3FuzzRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay3StaticRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay4FuzzRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay4StaticRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay5FuzzRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay5StaticRadio.toggled.connect(self.handle_payload_toggled)

        self.mainWindow.fuzzerHistoryClearButton.clicked.connect(self.fuzzer_history_clear_button_clicked)
        
        # inserted to initially fill the sequences box.
        # ToDo: Need to do this better
        self.mainWindow.mainTabWidget.currentChanged.connect(self.fill_sequences)
        self.mainWindow.stdFuzzTab.currentChanged.connect(self.fill_sequences)
        # self.mainWindow.webFuzzTab.currentChanged.connect(self.fill_payloads)
        self.mainWindow.wfStdAddButton.clicked.connect(self.insert_payload_marker)
        self.mainWindow.wfStdStartButton.clicked.connect(self.start_fuzzing_clicked)
        
        self.framework.subscribe_populate_webfuzzer_response_id(self.webfuzzer_populate_response_id)
        
        self.miniResponseRenderWidget = MiniResponseRenderWidget(self.framework, self.mainWindow.stdFuzzResultsTabWidget, self)
        
        self.re_request = re.compile(r'^(\S+)\s+((?:https?://(?:\S+\.)+\w+(?::\d+)?)?/.*)\s+HTTP/\d+\.\d+\s*$', re.I)
        self.re_request_cookie = re.compile(r'^Cookie:\s*(\S+)', re.I|re.M)
        self.re_replacement = re.compile(r'\$\{(\w+)\}')
        
        self.setup_fuzzer_tab()
        
        self.Attacks = Payloads.Payloads(self.framework)
        self.Attacks.list_files()
        
        # Fill the payloads combo boxes on init
        self.fill_payloads()
        self.pending_fuzz_requests = None

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.fill_fuzzers()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None
            
    def setup_fuzzer_tab(self):

        self.fuzzerHistoryDataModel = ResponsesDataModel.ResponsesDataModel(self.framework, self)
        self.mainWindow.fuzzerHistoryTreeView.setModel(self.fuzzerHistoryDataModel)
        self.mainWindow.fuzzerHistoryTreeView.doubleClicked.connect(self.fuzzer_history_item_double_clicked)
        self.mainWindow.fuzzerHistoryTreeView.clicked.connect(self.handle_fuzzer_history_clicked)
        self.responsesContextMenu = ResponsesContextMenuWidget(self.framework, self.fuzzerHistoryDataModel, self.mainWindow.fuzzerHistoryTreeView, self)

    def fill_fuzzers(self):
        history_items = []
        for row in self.Data.get_all_fuzzer_history(self.cursor):
            response_item = [m or '' for m in row]
            history_items.append(response_item)
        self.fuzzerHistoryDataModel.append_data(history_items)
        
    def fuzzer_history_item_double_clicked(self, index):
        Id = interface.index_to_id(self.fuzzerHistoryDataModel, index)
        if Id:
            dialog = RequestResponseDetailDialog(self.framework, Id, self.mainWindow)
            dialog.show()
            dialog.exec_()
            
    def fill_sequences(self):
        self.fill_sequences_combo_box(self.mainWindow.wfStdPreBox)
        self.fill_sequences_combo_box(self.mainWindow.wfStdPostBox)
        self.fill_sequences_combo_box(self.mainWindow.wfStdBox)
            
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
                
    def fill_payloads(self):
        self.fill_payload_combo_box(self.mainWindow.wfPay1PayloadBox)
        self.fill_payload_combo_box(self.mainWindow.wfPay2PayloadBox)
        self.fill_payload_combo_box(self.mainWindow.wfPay3PayloadBox)
        self.fill_payload_combo_box(self.mainWindow.wfPay4PayloadBox)
        self.fill_payload_combo_box(self.mainWindow.wfPay5PayloadBox)
    
    def fill_payload_combo_box(self, comboBox):
        
        selectedText = comboBox.currentText()
        comboBox.clear()
        # comboBox.addItem("SQLi")
        # comboBox.addItem("XSS")
        
        payloads = self.Attacks.list_files()
        for item in payloads:
            if item.startswith("."):
                pass
            else:
                comboBox.addItem(item)
        
        
    def create_payload_map(self):
        # create payload map from configuration tab
        
        payload_mapping = {}
        payloads = ["payload_1", "payload_2", "payload_3", "payload_4", "payload_5"]
        
        radioButtonList = [self.mainWindow.wfPay1FuzzRadio, self.mainWindow.wfPay2FuzzRadio, self.mainWindow.wfPay3FuzzRadio,
                           self.mainWindow.wfPay4FuzzRadio, self.mainWindow.wfPay5FuzzRadio, self.mainWindow.wfPay1StaticRadio,
                           self.mainWindow.wfPay2StaticRadio, self.mainWindow.wfPay3StaticRadio, self.mainWindow.wfPay4StaticRadio,
                           self.mainWindow.wfPay5StaticRadio]
        
        # Determine active payloads and map them
        if self.mainWindow.wfPay1FuzzRadio.isChecked():
            payload_mapping["payload_1"] = ("fuzz", str(self.mainWindow.wfPay1PayloadBox.currentText()))
        if self.mainWindow.wfPay1StaticRadio.isChecked():
            payload_mapping["payload_1"] = ("static", str(self.mainWindow.wfPay1StaticEdit.text()))
        if self.mainWindow.wfPay2FuzzRadio.isChecked():
            payload_mapping["payload_2"] = ("fuzz", str(self.mainWindow.wfPay2PayloadBox.currentText()))
        if self.mainWindow.wfPay2StaticRadio.isChecked():
            payload_mapping["payload_2"] = ("static", str(self.mainWindow.wfPay2StaticEdit.text()))
        if self.mainWindow.wfPay3FuzzRadio.isChecked():
            payload_mapping["payload_3"] = ("fuzz", str(self.mainWindow.wfPay3PayloadBox.currentText()))
        if self.mainWindow.wfPay3StaticRadio.isChecked():
            payload_mapping["payload_3"] = ("static", str(self.mainWindow.wfPay3StaticEdit.text()))
        if self.mainWindow.wfPay4FuzzRadio.isChecked():
            payload_mapping["payload_4"] = ("fuzz", str(self.mainWindow.wfPay4PayloadBox.currentText()))
        if self.mainWindow.wfPay4StaticRadio.isChecked():
            payload_mapping["payload_4"] = ("static", str(self.mainWindow.wfPay4StaticEdit.text()))
        if self.mainWindow.wfPay5FuzzRadio.isChecked():
            payload_mapping["payload_5"] = ("fuzz", str(self.mainWindow.wfPay5PayloadBox.currentText()))
        if self.mainWindow.wfPay5StaticRadio.isChecked():
            payload_mapping["payload_5"] = ("static", str(self.mainWindow.wfPay5StaticEdit.text()))
            
        return payload_mapping
        
    def set_combo_box_text(self, comboBox, selectedText):
        index = comboBox.findText(selectedText)
        if -1 != index:
            comboBox.setCurrentIndex(index)
        else:
            index = comboBox.addItem(selectedText)
            comboBox.setCurrentIndex(index)
                
    def handle_wfStdPreChk_stateChanged(self, state):
        self.mainWindow.wfStdPreBox.setEnabled(self.mainWindow.wfStdPreChk.isChecked())
    
    def handle_wfStdPostChk_stateChanged(self, state):
        self.mainWindow.wfStdPostBox.setEnabled(self.mainWindow.wfStdPostChk.isChecked())
        
    def handle_wfTempSeqChk_stateChanged(self, state):
        self.mainWindow.wfStdBox.setEnabled(self.mainWindow.wfTempSeqChk.isChecked())
        
    def handle_payload_toggled(self):
        self.mainWindow.wfPay1PayloadBox.setEnabled(self.mainWindow.wfPay1FuzzRadio.isChecked())
        self.mainWindow.wfPay1StaticEdit.setEnabled(self.mainWindow.wfPay1StaticRadio.isChecked())
        self.mainWindow.wfPay2PayloadBox.setEnabled(self.mainWindow.wfPay2FuzzRadio.isChecked())
        self.mainWindow.wfPay2StaticEdit.setEnabled(self.mainWindow.wfPay2StaticRadio.isChecked())
        self.mainWindow.wfPay3PayloadBox.setEnabled(self.mainWindow.wfPay3FuzzRadio.isChecked())
        self.mainWindow.wfPay3StaticEdit.setEnabled(self.mainWindow.wfPay3StaticRadio.isChecked())
        self.mainWindow.wfPay4PayloadBox.setEnabled(self.mainWindow.wfPay4FuzzRadio.isChecked())
        self.mainWindow.wfPay4StaticEdit.setEnabled(self.mainWindow.wfPay4StaticRadio.isChecked())
        self.mainWindow.wfPay5PayloadBox.setEnabled(self.mainWindow.wfPay5FuzzRadio.isChecked())
        self.mainWindow.wfPay5StaticEdit.setEnabled(self.mainWindow.wfPay5StaticRadio.isChecked())

    def handle_fuzzer_history_clicked(self):
        index = self.mainWindow.fuzzerHistoryTreeView.currentIndex()
        Id = interface.index_to_id(self.fuzzerHistoryDataModel, index)
        if Id:
            row = self.Data.read_responses_by_id(self.cursor, Id)
            if not row:
                return
            responseItems = [m or '' for m in list(row)]
            url = str(responseItems[ResponsesTable.URL])
            reqHeaders = str(responseItems[ResponsesTable.RES_HEADERS])
            reqData = str(responseItems[ResponsesTable.RES_DATA])
            contentType = str(responseItems[ResponsesTable.RES_CONTENT_TYPE])
            self.miniResponseRenderWidget.populate_response_text(url, reqHeaders, reqData, contentType)
        
    def webfuzzer_populate_response_id(self, Id):
        
        row = self.Data.read_responses_by_id(self.cursor, Id)
        if not row:
            return

        responseItems = [m or '' for m in list(row)]

        url = str(responseItems[ResponsesTable.URL])
        reqHeaders = str(responseItems[ResponsesTable.REQ_HEADERS])
        reqData = str(responseItems[ResponsesTable.REQ_DATA])
        method = str(responseItems[ResponsesTable.REQ_METHOD])
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
                if 'cookie' == lname:
                    template.write('${global_cookie_jar}\n')
                elif 'host' == lname:
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

        self.set_combo_box_text(self.mainWindow.stdFuzzerReqMethod, method.upper())
        self.mainWindow.wfStdUrlEdit.setText(url)
        self.mainWindow.wfStdEdit.setPlainText(template.getvalue())
        
    def insert_payload_marker(self):
        """ Inserts a payload marker at current cursor position """
        
        index = self.mainWindow.stdFuzzPayloadBox.currentIndex()
        curPayload = str(self.mainWindow.stdFuzzPayloadBox.itemText(index))
        
        self.mainWindow.wfStdEdit.textCursor().insertHtml("<font color='red'>${%s}</font>" % curPayload)
        
    def start_fuzzing_clicked(self):
        """ Start the fuzzing attack """

        if 'Cancel' == self.mainWindow.wfStdStartButton.text() and self.pending_fuzz_requests is not None:
            self.cancel_fuzz_requests = True
            for context, pending_request in self.pending_fuzz_requests.iteritems():
                pending_request.cancel()
            self.pending_fuzz_requests = None
            self.mainWindow.wfStdStartButton.setText('Start Attack')
            self.mainWindow.fuzzerStandardProgressBar.setValue(0)
            return
        
        self.pending_fuzz_requests = {}
        
        url = str(self.mainWindow.wfStdUrlEdit.text())
        # Will this work?
        self.framework.set_raft_config_value('wfStdUrlEdit', url)
        templateText = str(self.mainWindow.wfStdEdit.toPlainText())
        method = str(self.mainWindow.stdFuzzerReqMethod.currentText())
        
        replacements = self.build_replacements(method, url)

        sequenceId = None
        if self.mainWindow.wfStdPreChk.isChecked():
            sequenceId = str(self.mainWindow.wfStdPreBox.itemData(self.mainWindow.wfStdPreBox.currentIndex()).toString())
        
        # Fuzzing stuff
        payload_mapping = self.create_payload_map()

        
        
        re_parameters = re.compile(r'(\$\{\w+\})')
        re_parameter_name = re.compile(r'^\$\{(\w+)\}$')
        
        template_items = []
        parameter_names = set()
        for item in re_parameters.split(templateText):
            m = re_parameter_name.match(item)
            if m:
                name = m.group(1)
                if name in ["method", "request_uri", "global_cookie_jar", "user_agent", "host"]:
                    template_items.append(('text', item))
                else:
                    parameter_names.add(name)
                    template_items.append(('parameter', name)) # template item type and name
            else:
                template_items.append(('text', item)) # text replacement
                
        store_template_items = json.dumps(template_items)
        store_payload_mapping = json.dumps(payload_mapping)
        
        fuzz_payloads = {}
        
        for item in payload_mapping:
            if "fuzz" in payload_mapping[item]:
                newitem = payload_mapping[item]
                filename = newitem[1]
                values = self.Attacks.read_data(filename)
                fuzz_payloads[filename] = values
        
        test_slots = []
        counters = []
        tests_count = []
        total_tests = 1
        
        for name, payload_info in payload_mapping.iteritems():
            origin, payload_value = payload_info
            if 'static' == origin:
                # static payload value
                payloads = [payload_value]
            elif 'fuzz' == origin:
                payloads = fuzz_payloads[payload_value]
        
            total_tests *= len(payloads)
            test_slots.append((name, payloads))
            counters.append(0)
            tests_count.append(len(payloads))
            
        position_end = len(counters) - 1
        position = position_end

        self.miniResponseRenderWidget.clear_response_render()
        self.mainWindow.fuzzerStandardProgressBar.setMaximum(total_tests)
        
        finished = False
        first = True
        while not finished:
            data = {}
            for j in range(0, len(test_slots)):
                name, payloads = test_slots[j]
                data[name] = payloads[counters[j]]
        
            template_io = StringIO()
            for temp_type, temp_value in template_items:
                if 'text' == temp_type:
                    template_io.write(temp_value)
                elif 'parameter' == temp_type:
                    # assuming form encoding type with this hack
                    template_io.write(data[temp_value].replace(' ', '+').replace('&','%26').replace('=','%3D'))
        
            templateText = template_io.getvalue()
            context = uuid.uuid4().hex
            # print('%s%s%s' % ('-'*32, request, '-'*32))
            (method, url, headers, body, use_global_cookie_jar) = self.process_template(url, templateText, replacements)
            
            if first:
                    self.mainWindow.wfStdStartButton.setText('Cancel')
                    if use_global_cookie_jar:
                        self.fuzzRequesterCookieJar = self.framework.get_global_cookie_jar()
                    else:
                        self.fuzzRequesterCookieJar = InMemoryCookieJar(self.framework, self)
                    self.requestRunner = RequestRunner(self.framework, self)
                    self.requestRunner.setup(self.fuzzer_response_received, self.fuzzRequesterCookieJar, sequenceId)
                    first = False

            self.pending_fuzz_requests[context] = self.requestRunner.queue_request(method, url, headers, body, context)
            
            # increment to next test
            counters[position] = (counters[position] + 1) % (tests_count[position])
            while position >= 0 and counters[position] == 0:
                position -= 1
                counters[position] = (counters[position] + 1) % (tests_count[position])
        
            if position == -1:
                finished = True
            else:
                position = position_end        
        
       
    def build_replacements(self, method, url):
        replacements = {}
        splitted = urlparse.urlsplit(url)
        replacements['method'] = method.upper()
        replacements['url'] = url
        replacements['scheme'] = splitted.scheme or ''
        replacements['netloc'] = splitted.netloc or ''
        replacements['host'] = splitted.hostname or ''
        replacements['path'] = splitted.path or ''
        replacements['query'] = splitted.query or ''
        replacements['fragment'] = splitted.fragment or ''
        replacements['request_uri'] = urlparse.urlunsplit(('', '', splitted.path, splitted.query, ''))
        replacements['user_agent'] = self.framework.useragent()
        return replacements

    def process_template(self, url, template, replacements):
        
        # Start of old
        method, uri = '' ,''
        headers, body = '', ''
        use_global_cookie_jar = False

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
            print(line)
            if not line:
                break
            if '$' in line:
                if '${global_cookie_jar}' == line:
                    use_global_cookie_jar = True
                    continue
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

        return (method, url, headers_dict, body, use_global_cookie_jar)
        
    def fuzzer_history_clear_button_clicked(self):
        self.Data.clear_fuzzer_history(self.cursor)
        self.fuzzerHistoryDataModel.clearModel()

    def fuzzer_response_received(self, response_id, context):
        self.mainWindow.fuzzerStandardProgressBar.setValue(self.mainWindow.fuzzerStandardProgressBar.value()+1)
        context = str(context)
        if self.pending_fuzz_requests is not None:
            try:
                self.pending_fuzz_requests.pop(context)
            except KeyError, e:
                pass
        if 0 != response_id:
            row = self.Data.read_responses_by_id(self.cursor, response_id)
            if row:
                response_item = [m or '' for m in row]
                self.Data.insert_fuzzer_history(self.cursor, response_id)
                self.fuzzerHistoryDataModel.append_data([response_item])

        finished = False
        if self.pending_fuzz_requests is None or len(self.pending_fuzz_requests) == 0:
            self.mainWindow.fuzzerStandardProgressBar.setValue(self.mainWindow.fuzzerStandardProgressBar.maximum())
            finished = True
        elif self.mainWindow.fuzzerStandardProgressBar.value() == self.mainWindow.fuzzerStandardProgressBar.maximum():
            finished = True
        if finished:
            self.mainWindow.wfStdStartButton.setText('Start Attack')
        
