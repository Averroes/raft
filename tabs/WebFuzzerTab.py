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


from io import StringIO
from urllib import parse as urlparse
import uuid
import re
import json
import os

from actions import interface
from utility import ScintillaHelpers

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
from dialogs import ConfirmDialog

from core.fuzzer.TemplateDefinition import TemplateDefinition
from core.fuzzer.TemplateItem import TemplateItem

from utility.ScriptLoader import ScriptLoader

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
        self.mainWindow.wfPay1DynamicRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay2FuzzRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay2StaticRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay2DynamicRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay3FuzzRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay3StaticRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay3DynamicRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay4FuzzRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay4StaticRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay4DynamicRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay5FuzzRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay5StaticRadio.toggled.connect(self.handle_payload_toggled)
        self.mainWindow.wfPay5DynamicRadio.toggled.connect(self.handle_payload_toggled)

        self.mainWindow.fuzzerHistoryClearButton.clicked.connect(self.fuzzer_history_clear_button_clicked)
        
        # inserted to initially fill the sequences box.
        # ToDo: Need to do this better
        self.mainWindow.mainTabWidget.currentChanged.connect(self.handle_mainTabWidget_currentChanged)
        self.mainWindow.webFuzzTab.currentChanged.connect(self.handle_webFuzzTab_currentChanged)
        self.mainWindow.stdFuzzTab.currentChanged.connect(self.handle_stdFuzzTab_currentChanged)
        # self.mainWindow.webFuzzTab.currentChanged.connect(self.fill_payloads)
        self.mainWindow.wfStdAddButton.clicked.connect(self.insert_payload_marker)
        self.mainWindow.wfStdStartButton.clicked.connect(self.start_fuzzing_clicked)
        self.mainWindow.wfDataDictonaryAddButton.clicked.connect(self.handle_wfDataDictonaryAddButton_clicked)
        
        self.framework.subscribe_populate_webfuzzer_response_id(self.webfuzzer_populate_response_id)
        self.framework.subscribe_sequences_changed(self.fill_sequences)
        
        self.mainWindow.wfFunctionsComboBox.activated.connect(self.fill_function_edit)
        
        self.mainWindow.wfFunctionsSaveButton.clicked.connect(self.save_function_file)
        self.mainWindow.wfFunctionsDeleteButton.clicked.connect(self.del_function_file)
        
        self.miniResponseRenderWidget = MiniResponseRenderWidget(self.framework, self.mainWindow.stdFuzzResultsTabWidget, True, self)
        
        self.re_request = re.compile(r'^(\S+)\s+((?:https?://(?:\S+\.)+\w+(?::\d+)?)?/.*)\s+HTTP/\d+\.\d+\s*$', re.I)
        self.re_request_cookie = re.compile(r'^Cookie:\s*(\S+)', re.I|re.M)
        self.re_replacement = re.compile(r'\$\{(\w+)\}')

        self.setup_fuzzer_tab()

        self.setup_functions_tab()
        
        self.functions_dir = os.path.join(self.framework.get_data_dir(), 'functions')
        
        self.Attacks = Payloads.Payloads(self.framework)
        self.Attacks.list_files()
        
        # Fill the payloads combo boxes on init
        self.fill_payloads()
        self.pending_fuzz_requests = None
        
        # Fill the functions combo box on init
        self.fill_function_combo_box()

        self.mainWindow.wfDataDictionaryDataTable.setColumnCount(2)
        self.mainWindow.wfDataDictionaryDataTable.setHorizontalHeaderLabels(['Replacement', 'Value'])

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.fill_fuzzers()
        self.fill_standard_edits()
        self.fill_config_edits()
        self.restore_data_dictionary()

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
        self.mainWindow.fuzzerHistoryTreeView.activated.connect(self.handle_fuzzer_history_clicked)
        self.responsesContextMenu = ResponsesContextMenuWidget(self.framework, self.fuzzerHistoryDataModel, self.mainWindow.fuzzerHistoryTreeView, self)
        self.responsesContextMenu.set_currentChanged_callback(self.fill_fuzzer_history)

    def setup_functions_tab(self):
        self.functionsLayout = self.mainWindow.wfFunctionsEditPlaceholder.layout()
        if not self.functionsLayout:
            self.functionsLayout = QVBoxLayout(self.mainWindow.wfFunctionsEditPlaceholder)
        self.functionsEditScintilla = Qsci.QsciScintilla(self.mainWindow.wfFunctionsEditPlaceholder)

        ScintillaHelpers.SetScintillaProperties(self.framework, self.functionsEditScintilla, 'python')
        self.functionsEditScintilla.setAutoIndent(True)
        self.functionsLayout.addWidget(self.functionsEditScintilla)
        self.framework.subscribe_zoom_in(self.edit_function_zoom_in)
        self.framework.subscribe_zoom_out(self.edit_function_zoom_out)

    def edit_function_zoom_in(self):
        self.functionsEditScintilla.zoomIn()

    def edit_function_zoom_out(self):
        self.functionsEditScintilla.zoomOut()

    def fill_fuzzers(self):
        history_items = []
        for row in self.Data.get_all_fuzzer_history(self.cursor):
            response_item = [m or '' for m in row]
            history_items.append(response_item)
        self.fuzzerHistoryDataModel.append_data(history_items)
        self.fill_sequences()

    def fill_standard_edits(self):
        self.mainWindow.wfStdUrlEdit.setText(self.framework.get_raft_config_value('WebFuzzer.Standard.RequestUrl'))
        self.mainWindow.wfStdEdit.document().setHtml(self.framework.get_raft_config_value('WebFuzzer.Standard.TemplateHtml'))
        index = self.mainWindow.stdFuzzerReqMethod.findText(self.framework.get_raft_config_value('WebFuzzer.Standard.Method'))
        if index != -1:
            self.mainWindow.stdFuzzerReqMethod.setCurrentIndex(index)

        self.mainWindow.wfStdPreChk.setChecked(self.framework.get_raft_config_value('WebFuzzer.Standard.PreSequenceEnabled', bool))
        index = self.mainWindow.wfStdPreBox.findText(self.framework.get_raft_config_value('WebFuzzer.Standard.PreSequenceId'))
        if index != -1:
            self.mainWindow.wfStdPreBox.setCurrentIndex(index)

        self.mainWindow.wfStdPostChk.setChecked(self.framework.get_raft_config_value('WebFuzzer.Standard.PostSequenceEnabled', bool))
        index = self.mainWindow.wfStdPostBox.findText(self.framework.get_raft_config_value('WebFuzzer.Standard.PostSequenceId'))
        if index != -1:
            self.mainWindow.wfStdPostBox.setCurrentIndex(index)

    def fill_config_edits(self):
        self.fill_config_edit_item('Payload1', self.mainWindow.wfPay1FuzzRadio, self.mainWindow.wfPay1PayloadBox, self.mainWindow.wfPay1StaticRadio, self.mainWindow.wfPay1DynamicRadio, self.mainWindow.wfPay1StaticEdit)
        self.fill_config_edit_item('Payload2', self.mainWindow.wfPay2FuzzRadio, self.mainWindow.wfPay2PayloadBox, self.mainWindow.wfPay2StaticRadio, self.mainWindow.wfPay2DynamicRadio, self.mainWindow.wfPay2StaticEdit)
        self.fill_config_edit_item('Payload3', self.mainWindow.wfPay3FuzzRadio, self.mainWindow.wfPay3PayloadBox, self.mainWindow.wfPay3StaticRadio, self.mainWindow.wfPay3DynamicRadio, self.mainWindow.wfPay3StaticEdit)
        self.fill_config_edit_item('Payload4', self.mainWindow.wfPay4FuzzRadio, self.mainWindow.wfPay4PayloadBox, self.mainWindow.wfPay4StaticRadio, self.mainWindow.wfPay4DynamicRadio, self.mainWindow.wfPay4StaticEdit)
        self.fill_config_edit_item('Payload5', self.mainWindow.wfPay5FuzzRadio, self.mainWindow.wfPay5PayloadBox, self.mainWindow.wfPay5StaticRadio, self.mainWindow.wfPay5DynamicRadio, self.mainWindow.wfPay5StaticEdit)
        
    def fill_config_edit_item(self, payload_item, fuzzRadio, payloadBox, staticRadio, dynamicRadio, staticEdit):
        fuzzRadio.setChecked(self.framework.get_raft_config_value('WebFuzzer.Config.{0}FuzzSelected'.format(payload_item), bool))
        index = payloadBox.findText(self.framework.get_raft_config_value('WebFuzzer.Config.{0}FuzzPayload'.format(payload_item)))
        if index != -1:
            payloadBox.setCurrentIndex(index)
        staticRadio.setChecked(self.framework.get_raft_config_value('WebFuzzer.Config.{0}StaticSelected'.format(payload_item), bool))
        dynamicRadio.setChecked(self.framework.get_raft_config_value('WebFuzzer.Config.{0}DynamicSelected'.format(payload_item), bool))
        staticEdit.setText(self.framework.get_raft_config_value('WebFuzzer.Config.{0}StaticEdit'.format(payload_item)))

    def fuzzer_history_item_double_clicked(self, index):
        Id = interface.index_to_id(self.fuzzerHistoryDataModel, index)
        if Id:
            dialog = RequestResponseDetailDialog(self.framework, Id, self.mainWindow)
            dialog.show()
            dialog.exec_()

    def handle_mainTabWidget_currentChanged(self):
        self.save_configuration_values()

    def handle_stdFuzzTab_currentChanged(self):
        self.save_standard_configuration()

    def handle_webFuzzTab_currentChanged(self):
        self.save_configuration_values()
            
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
        
        payloads = self.Attacks.list_files()
        for item in payloads:
            if item.startswith("."):
                pass
            else:
                comboBox.addItem(item)
                
    def fill_payload_combo_box_function(self, comboBox):
        
        selectedText = comboBox.currentText()
        comboBox.clear()
        
        functions = self.Attacks.list_function_files()
        for item in functions:
            if item.startswith("."):
                pass
            else:
                comboBox.addItem(item)
    
                
    def fill_function_combo_box(self):
        comboBox = self.mainWindow.wfFunctionsComboBox
        comboBox.clear()
        
        functions = self.Attacks.list_function_files()
        for item in functions:
            if item.startswith("."):
                pass
            else:
                comboBox.addItem(item)
                
    def fill_function_edit(self):
        
        filename = self.mainWindow.wfFunctionsComboBox.currentText()
        
        func = self.Attacks.read_function(filename)
        
        # Clear the Scintilla widget
        self.functionsEditScintilla.clear()
        
        for line in func:
            self.functionsEditScintilla.append(line.decode("utf8"))
            
    def save_function_file(self):
        
        function_file = self.mainWindow.wfFunctionsComboBox.currentText()
        content = self.functionsEditScintilla.text()
        
        self.Attacks.save_function(function_file, content)
    
            
    def del_function_file(self):
        
        # Gets the current name of the file selected in the combobox
        filename = self.mainWindow.wfFunctionsComboBox.currentText()
        path = self.functions_dir
        
        message = "Are you sure you want to delete: {0}".format(filename)
        
        response = ConfirmDialog.display_confirm_dialog(self.mainWindow, message)
        
        if response == True:
            os.remove(os.path.join(path,filename))
            
            self.fill_function_combo_box()
                    
            # Clear the items from the scintilla widget
            #ToDo: This should be the default data for the function
            self.functionsEditScintilla.clear()
    
        
    def create_payload_map(self):
        # create payload map from configuration tab
        
        payload_mapping = {}

        payload_config_items = (
            ("payload_1", 
             "fuzz", self.mainWindow.wfPay1FuzzRadio, self.mainWindow.wfPay1PayloadBox,
             "static", self.mainWindow.wfPay1StaticRadio, self.mainWindow.wfPay1StaticEdit,
             "dynamic", self.mainWindow.wfPay1DynamicRadio, self.mainWindow.wfPay1StaticEdit,
             ),
            ("payload_2", 
             "fuzz", self.mainWindow.wfPay2FuzzRadio, self.mainWindow.wfPay2PayloadBox,
             "static", self.mainWindow.wfPay2StaticRadio, self.mainWindow.wfPay2StaticEdit,
             "dynamic", self.mainWindow.wfPay2DynamicRadio, self.mainWindow.wfPay2StaticEdit,
             ),
            ("payload_3", 
             "fuzz", self.mainWindow.wfPay3FuzzRadio, self.mainWindow.wfPay3PayloadBox,
             "static", self.mainWindow.wfPay3StaticRadio, self.mainWindow.wfPay3StaticEdit,
             "dynamic", self.mainWindow.wfPay3DynamicRadio, self.mainWindow.wfPay3StaticEdit,
             ),
            ("payload_4", 
             "fuzz", self.mainWindow.wfPay4FuzzRadio, self.mainWindow.wfPay4PayloadBox,
             "static", self.mainWindow.wfPay4StaticRadio, self.mainWindow.wfPay4StaticEdit,
             "dynamic", self.mainWindow.wfPay4DynamicRadio, self.mainWindow.wfPay4StaticEdit,
             ),
            ("payload_5", 
             "fuzz", self.mainWindow.wfPay5FuzzRadio, self.mainWindow.wfPay5PayloadBox,
             "static", self.mainWindow.wfPay5StaticRadio, self.mainWindow.wfPay5StaticEdit,
             "dynamic", self.mainWindow.wfPay5DynamicRadio, self.mainWindow.wfPay5StaticEdit,
             ),
            )
        
        # Determine active payloads and map them
        for config_item in payload_config_items:
            payload_item = config_item[0]
            payload_mapping[payload_item] = ('none', '')
            for offset in (1, 4, 7):
                if config_item[offset+1].isChecked():
                    payload_type = config_item[offset]
#                    print((payload_type, offset))
                    if payload_type == "dynamic":
                        payload_mapping[payload_item] = (payload_type, str(config_item[offset+2].text()), config_item[3].currentText())
                    elif payload_type == "fuzz":
                        payload_mapping[payload_item] = (payload_type, str(config_item[offset+2].currentText()), '')
                    else:
                        payload_mapping[payload_item] = (payload_type, str(config_item[offset+2].text()), '')
                    break

        return payload_mapping

    def create_functions(self):
        self.global_ns = self.local_ns = {} 
        functions = [
'''
import urllib.parse
import re
import random

def url_encode(input):
   return urllib.parse.quote(input)

re_alert_mangler = re.compile(r'alert\([^(]+\)', re.I)

def randomize_alert_replace(m):
   return 'alert(%d.%d)' % (random.randint(0,99999), random.randint(0,99999))

def randomize_alert(input):
   return re_alert_mangler.sub(randomize_alert_replace, input)
'''
]
        for func_str in functions:
            compiled = compile(func_str, '<string>', 'exec')
            exec(compiled, self.global_ns, self.local_ns)
        
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
        self.mainWindow.wfPay1PayloadBox.setEnabled(self.mainWindow.wfPay1FuzzRadio.isChecked() or self.mainWindow.wfPay1DynamicRadio.isChecked())
        self.mainWindow.wfPay1StaticEdit.setEnabled(self.mainWindow.wfPay1StaticRadio.isChecked() or self.mainWindow.wfPay1DynamicRadio.isChecked())
        # self.mainWindow.wfPay1PayloadBox.setEnabled(self.mainWindow.wfPay1DynamicRadio.isChecked()) or self.fill_payload_combo_box_function(self.mainWindow.wfPay1PayloadBox)
        self.mainWindow.wfPay2PayloadBox.setEnabled(self.mainWindow.wfPay2FuzzRadio.isChecked() or self.mainWindow.wfPay2DynamicRadio.isChecked())
        self.mainWindow.wfPay2StaticEdit.setEnabled(self.mainWindow.wfPay2StaticRadio.isChecked() or self.mainWindow.wfPay2DynamicRadio.isChecked()) 
        self.mainWindow.wfPay3PayloadBox.setEnabled(self.mainWindow.wfPay3FuzzRadio.isChecked() or self.mainWindow.wfPay3DynamicRadio.isChecked())
        self.mainWindow.wfPay3StaticEdit.setEnabled(self.mainWindow.wfPay3StaticRadio.isChecked() or self.mainWindow.wfPay3DynamicRadio.isChecked()) 
        self.mainWindow.wfPay4PayloadBox.setEnabled(self.mainWindow.wfPay4FuzzRadio.isChecked() or self.mainWindow.wfPay4DynamicRadio.isChecked())
        self.mainWindow.wfPay4StaticEdit.setEnabled(self.mainWindow.wfPay4StaticRadio.isChecked() or self.mainWindow.wfPay4DynamicRadio.isChecked()) 
        self.mainWindow.wfPay5PayloadBox.setEnabled(self.mainWindow.wfPay5FuzzRadio.isChecked() or self.mainWindow.wfPay5DynamicRadio.isChecked())
        self.mainWindow.wfPay5StaticEdit.setEnabled(self.mainWindow.wfPay5StaticRadio.isChecked() or self.mainWindow.wfPay5DynamicRadio.isChecked()) 
        
        # Determine if fuzz or dynamic is selected and change combo box items
        if self.mainWindow.wfPay1FuzzRadio.isChecked():
            self.fill_payload_combo_box(self.mainWindow.wfPay1PayloadBox)
        if self.mainWindow.wfPay1DynamicRadio.isChecked():
            self.fill_payload_combo_box_function(self.mainWindow.wfPay1PayloadBox)
        if self.mainWindow.wfPay2FuzzRadio.isChecked():
            self.fill_payload_combo_box(self.mainWindow.wfPay2PayloadBox)
        if self.mainWindow.wfPay2DynamicRadio.isChecked():
            self.fill_payload_combo_box_function(self.mainWindow.wfPay2PayloadBox)
        if self.mainWindow.wfPay3FuzzRadio.isChecked():
            self.fill_payload_combo_box(self.mainWindow.wfPay3PayloadBox)
        if self.mainWindow.wfPay3DynamicRadio.isChecked():
            self.fill_payload_combo_box_function(self.mainWindow.wfPay3PayloadBox)
        if self.mainWindow.wfPay4FuzzRadio.isChecked():
            self.fill_payload_combo_box(self.mainWindow.wfPay4PayloadBox)
        if self.mainWindow.wfPay4DynamicRadio.isChecked():
            self.fill_payload_combo_box_function(self.mainWindow.wfPay4PayloadBox)
        if self.mainWindow.wfPay5FuzzRadio.isChecked():
            self.fill_payload_combo_box(self.mainWindow.wfPay5PayloadBox)
        if self.mainWindow.wfPay5DynamicRadio.isChecked():
            self.fill_payload_combo_box_function(self.mainWindow.wfPay5PayloadBox)
            

    def handle_fuzzer_history_clicked(self):
        index = self.mainWindow.fuzzerHistoryTreeView.currentIndex()
        self.fill_fuzzer_history(index)

    def fill_fuzzer_history(self, index):
        Id = interface.index_to_id(self.fuzzerHistoryDataModel, index)
        if Id:
            row = self.Data.read_responses_by_id(self.cursor, Id)
            if not row:
                return
            responseItems = interface.data_row_to_response_items(row)
            url = responseItems[ResponsesTable.URL]
            reqHeaders = responseItems[ResponsesTable.REQ_HEADERS]
            reqData = responseItems[ResponsesTable.REQ_DATA]
            resHeaders = responseItems[ResponsesTable.RES_HEADERS]
            resData = responseItems[ResponsesTable.RES_DATA]
            contentType = responseItems[ResponsesTable.RES_CONTENT_TYPE]
            self.miniResponseRenderWidget.populate_response_content(url, reqHeaders, reqData, resHeaders, resData, contentType)

    def webfuzzer_populate_response_id(self, Id):

        self.clear_data_dictionary()
        
        row = self.Data.read_responses_by_id(self.cursor, Id)
        if not row:
            return

        responseItems = interface.data_row_to_response_items(row)

        url = responseItems[ResponsesTable.URL]
        reqHeaders = responseItems[ResponsesTable.REQ_HEADERS].decode('utf-8', 'ignore')
        reqData = responseItems[ResponsesTable.REQ_DATA].decode('utf-8', 'ignore')
        method = responseItems[ResponsesTable.REQ_METHOD]
        splitted = urlparse.urlsplit(url)
        
        # Create a new parsed object removing the scheme and netloc
        base_url = urlparse.urlunsplit((splitted[0], splitted[1], splitted[2], '', ''))
        req_loc = ("", "", "", splitted.query, splitted.fragment)

        useragent = self.framework.useragent()
        has_cookie = False
        template = StringIO()
        template.write('${method} ${request_uri}%s HTTP/1.1\n' % urlparse.urlunsplit(req_loc))
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

        self.set_combo_box_text(self.mainWindow.stdFuzzerReqMethod, method.upper())
        self.mainWindow.wfStdUrlEdit.setText(base_url)
        self.mainWindow.wfStdEdit.setPlainText(template.getvalue())
        
    def insert_payload_marker(self):
        """ Inserts a payload marker at current cursor position """
        
        index = self.mainWindow.stdFuzzPayloadBox.currentIndex()
        curPayload = str(self.mainWindow.stdFuzzPayloadBox.itemText(index))
        currentText = self.mainWindow.wfStdEdit.textCursor().selectedText()
        
        self.store_in_data_dictionary(curPayload, currentText)
        self.mainWindow.wfStdEdit.textCursor().insertHtml("<font color='red'>${%s}</font>" % curPayload)
        self.save_configuration_values()

    def clear_data_dictionary(self):
        tableWidget = self.mainWindow.wfDataDictionaryDataTable
        while tableWidget.rowCount() > 0:
            tableWidget.removeRow(0)
        self.save_data_dictionary_to_config()

    def store_in_data_dictionary(self, replacement, value):
        # TODO: currently logic allows for duplicate values to appear
        tableWidget = self.mainWindow.wfDataDictionaryDataTable
        row = tableWidget.rowCount()
        tableWidget.insertRow(row)
        tableWidget.setItem(row, 0, QTableWidgetItem(replacement))
        tableWidget.setItem(row, 1, QTableWidgetItem(value))
        self.save_data_dictionary_to_config()

    def save_data_dictionary_to_config(self):
        ddict = self.get_values_from_data_dictionary()
        dd_data = json.dumps(ddict)
        self.framework.set_raft_config_value('WebFuzzer.Standard.DataDictionary', dd_data)

    def restore_data_dictionary(self):
        dd_data = self.framework.get_raft_config_value('WebFuzzer.Standard.DataDictionary', '')
        if dd_data:
            tableWidget = self.mainWindow.wfDataDictionaryDataTable
            obj = json.loads(dd_data)
            for name, value in obj.items():
                row = tableWidget.rowCount()
                tableWidget.insertRow(row)
                tableWidget.setItem(row, 0, QTableWidgetItem(name))
                tableWidget.setItem(row, 1, QTableWidgetItem(value))
        
    def get_values_from_data_dictionary(self):
        tableWidget = self.mainWindow.wfDataDictionaryDataTable
        ddict = {}
        for rindex in range(0, tableWidget.rowCount()):
            name = tableWidget.item(rindex, 0).text()
            value = tableWidget.item(rindex, 1).text()
            ddict[name] = value

        return ddict

    def handle_wfDataDictonaryAddButton_clicked(self):
        name = self.mainWindow.wfDataDictionaryDataName.text()
        value = self.mainWindow.wfDataDictionaryDataValue.text()
        self.store_in_data_dictionary(name, value)

    def save_configuration_values(self):
        self.save_standard_configuration()
        self.save_config_configuration()

    def save_standard_configuration(self):
        url = str(self.mainWindow.wfStdUrlEdit.text())
        templateHtml = str(self.mainWindow.wfStdEdit.document().toHtml())
        method = str(self.mainWindow.stdFuzzerReqMethod.currentText())

        self.framework.set_raft_config_value('WebFuzzer.Standard.RequestUrl', url)
        self.framework.set_raft_config_value('WebFuzzer.Standard.TemplateHtml', templateHtml)
        self.framework.set_raft_config_value('WebFuzzer.Standard.Method', method)

        self.framework.set_raft_config_value('WebFuzzer.Standard.PreSequenceEnabled', self.mainWindow.wfStdPreChk.isChecked())
        self.framework.set_raft_config_value('WebFuzzer.Standard.PreSequenceId', self.mainWindow.wfStdPreBox.itemData(self.mainWindow.wfStdPreBox.currentIndex()))

        self.framework.set_raft_config_value('WebFuzzer.Standard.PostSequenceEnabled', self.mainWindow.wfStdPostChk.isChecked())
        self.framework.set_raft_config_value('WebFuzzer.Standard.PostSequenceId', self.mainWindow.wfStdPostBox.itemData(self.mainWindow.wfStdPostBox.currentIndex()))

    def save_config_configuration(self):
        self.save_config_configuration_item('Payload1', self.mainWindow.wfPay1FuzzRadio, self.mainWindow.wfPay1PayloadBox, self.mainWindow.wfPay1StaticRadio, self.mainWindow.wfPay1DynamicRadio, self.mainWindow.wfPay1StaticEdit)
        self.save_config_configuration_item('Payload2', self.mainWindow.wfPay2FuzzRadio, self.mainWindow.wfPay2PayloadBox, self.mainWindow.wfPay2StaticRadio, self.mainWindow.wfPay2DynamicRadio, self.mainWindow.wfPay2StaticEdit)
        self.save_config_configuration_item('Payload3', self.mainWindow.wfPay3FuzzRadio, self.mainWindow.wfPay3PayloadBox, self.mainWindow.wfPay3StaticRadio, self.mainWindow.wfPay3DynamicRadio, self.mainWindow.wfPay3StaticEdit)
        self.save_config_configuration_item('Payload4', self.mainWindow.wfPay4FuzzRadio, self.mainWindow.wfPay4PayloadBox, self.mainWindow.wfPay4StaticRadio, self.mainWindow.wfPay4DynamicRadio, self.mainWindow.wfPay4StaticEdit)
        self.save_config_configuration_item('Payload5', self.mainWindow.wfPay5FuzzRadio, self.mainWindow.wfPay5PayloadBox, self.mainWindow.wfPay5StaticRadio, self.mainWindow.wfPay5DynamicRadio, self.mainWindow.wfPay5StaticEdit)

    def save_config_configuration_item(self, payload_item, fuzzRadio, payloadBox, staticRadio, dynamicRadio, staticEdit):
        self.framework.set_raft_config_value('WebFuzzer.Config.{0}FuzzSelected'.format(payload_item), fuzzRadio.isChecked())
        self.framework.set_raft_config_value('WebFuzzer.Config.{0}FuzzPayload'.format(payload_item), str(payloadBox.currentText()))
        self.framework.set_raft_config_value('WebFuzzer.Config.{0}StaticSelected'.format(payload_item), staticRadio.isChecked())
        self.framework.set_raft_config_value('WebFuzzer.Config.{0}DynamicSelected'.format(payload_item), dynamicRadio.isChecked())
        self.framework.set_raft_config_value('WebFuzzer.Config.{0}StaticEdit'.format(payload_item), staticEdit.text())
        
    def start_fuzzing_clicked(self):
        """ Start the fuzzing attack """

        if 'Cancel' == self.mainWindow.wfStdStartButton.text() and self.pending_fuzz_requests is not None:
            self.cancel_fuzz_requests = True
            for context, pending_request in self.pending_fuzz_requests.items():
                pending_request.cancel()
            self.pending_fuzz_requests = None
            self.mainWindow.wfStdStartButton.setText('Start Attack')
            self.mainWindow.fuzzerStandardProgressBar.setValue(0)
            return
        
        self.pending_fuzz_requests = {}
        
        url = str(self.mainWindow.wfStdUrlEdit.text())
        templateText = str(self.mainWindow.wfStdEdit.toPlainText())
        method = str(self.mainWindow.stdFuzzerReqMethod.currentText())

        self.save_standard_configuration()
        
        replacements = self.build_replacements(method, url)

        sequenceId = None
        if self.mainWindow.wfStdPreChk.isChecked():
            sequenceId = self.mainWindow.wfStdPreBox.itemData(self.mainWindow.wfStdPreBox.currentIndex())

        postSequenceId = None
        if self.mainWindow.wfStdPostChk.isChecked():
            postSequenceId = self.mainWindow.wfStdPostBox.itemData(self.mainWindow.wfStdPostBox.currentIndex())
        
        # Fuzzing stuff
        payload_mapping = self.create_payload_map()
#        print(payload_mapping)
        self.create_functions()
        
        template_definition = TemplateDefinition(templateText)

        template_items = template_definition.template_items
###        print(template_items)
        parameter_names = template_definition.parameter_names

        self.global_ns = self.local_ns = {}
        scriptLoader = ScriptLoader()

        errors = []
        fuzz_payloads = {}
        for name, payload_info in payload_mapping.items():
            if name in parameter_names:
                payload_type, payload_value, payload_file = payload_info
                if 'fuzz' == payload_type:
                    filename = payload_value
                    values = self.Attacks.read_data(filename)
                    fuzz_payloads[name] = values
                elif 'dynamic' == payload_type:
                    target = payload_file
                    # TODO: should this come from saved file or current Scintilla values (?)
                    script_env = scriptLoader.load_from_file(os.path.join(self.functions_dir, target), self.global_ns, self.local_ns)
                    expression = payload_value
                    if not expression.endswith('()'):
                        expression += '()'
                    eval_result = eval(expression, self.global_ns, self.local_ns)
                    fuzz_payloads[name] = [str(v) for v in eval_result]
                elif 'static' == payload_type:
                    pass
                elif 'none' == payload_type:
                    # unconfigured payload
                    errors.append(name)
        
        test_slots = []
        counters = []
        tests_count = []
        total_tests = 1
        
        for name, payload_info in payload_mapping.items():
            if name in parameter_names:
                payload_type, payload_value, payload_file = payload_info
                if 'static' == payload_type:
                    # static payload value
                    payloads = [payload_value]
                elif 'fuzz' == payload_type:
                    payloads = fuzz_payloads[name]
                elif 'dynamic' == payload_type:
                    payloads = fuzz_payloads[name]

                total_tests *= len(payloads)
                test_slots.append((name, payloads))
                counters.append(0)
                tests_count.append(len(payloads))
            
        position_end = len(counters) - 1
        position = position_end

        self.miniResponseRenderWidget.clear_response_render()
        self.mainWindow.fuzzerStandardProgressBar.setValue(0)
        self.mainWindow.fuzzerStandardProgressBar.setMaximum(total_tests)
        
        finished = False
        first = True
        while not finished:
            data = {}
            for j in range(0, len(test_slots)):
                name, payloads = test_slots[j]
                data[name] = payloads[counters[j]]
        
            template_io = StringIO()
            self.apply_template_parameters(template_io, data, template_items)
        
            templateText = template_io.getvalue()
            context = uuid.uuid4().hex
            # print('%s%s%s' % ('-'*32, request, '-'*32))
            use_global_cookie_jar = self.mainWindow.webFuzzerUseGlobalCookieJar.isChecked()
            (method, url, headers, body) = self.process_template(url, templateText, replacements)
            
            if first:
                    self.mainWindow.wfStdStartButton.setText('Cancel')
                    if use_global_cookie_jar:
                        self.fuzzRequesterCookieJar = self.framework.get_global_cookie_jar()
                    else:
                        self.fuzzRequesterCookieJar = InMemoryCookieJar(self.framework, self)
                    self.requestRunner = RequestRunner(self.framework, self)
                    self.requestRunner.setup(self.fuzzer_response_received, self.fuzzRequesterCookieJar, sequenceId, postSequenceId)
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

    def apply_template_parameters(self, template_io, data, template_items):

        for item in template_items:
            if item.is_text():
                template_io.write(item.item_value)
            elif item.is_builtin():
                template_io.write('${'+item.item_value+'}')
            elif item.is_payload():
                template_io.write(data[item.item_value])
            elif item.is_function():
                temp_io = StringIO()
                self.apply_template_parameters(temp_io, data, item.items)
                temp_result = temp_io.getvalue()
                temp_io = None
                result = eval('%s(%s)' % (item.item_value, repr(temp_result)), self.global_ns, self.local_ns)
                template_io.write(str(result))
            else:
                raise Exception('unsupported template parameters: ' + repr(item))
       
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
        replacements['request_uri'] = url
        replacements['user_agent'] = self.framework.useragent()
        return replacements

    def process_template(self, url, template, replacements):
        
        # Start of old
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
#            print(line)
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
        
    def fuzzer_history_clear_button_clicked(self):
        self.Data.clear_fuzzer_history(self.cursor)
        self.fuzzerHistoryDataModel.clearModel()

    def fuzzer_response_received(self, response_id, context):
        self.mainWindow.fuzzerStandardProgressBar.setValue(self.mainWindow.fuzzerStandardProgressBar.value()+1)
        context = str(context)
        if self.pending_fuzz_requests is not None:
            try:
                self.pending_fuzz_requests.pop(context)
            except KeyError as e:
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
        
