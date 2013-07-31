#
# configuration dialog
#
# Authors: 
#          Gregory Fleischer (gfleischer@gmail.com)
#          Nathan Hamiel
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

from PyQt4.QtCore import (Qt, SIGNAL, QObject)
from PyQt4.QtGui import *

from ui import ConfigDialog
from tabs import DataBankTab
from dialogs import ConfirmDialog
from dialogs.SimpleDialog import SimpleDialog
from dialogs.ProgressDialog import ProgressDialog

from core.fuzzer import Payloads

import os
import shutil
import json

class ConfigDialog(QDialog, ConfigDialog.Ui_configDialog):
    """ The Config Dialog """
    
    def __init__(self, framework, parent=None):
        super(ConfigDialog, self).__init__(parent)
        self.setupUi(self)

        self.framework = framework
        self.payloads_dir = os.path.join(self.framework.get_data_dir(), 'payloads')
        self.Progress = ProgressDialog()

        self.buttonBox.clicked.connect(self.handle_buttonBox_clicked)

        self.checkBoxUseProxy.stateChanged.connect(self.handle_useProxy_stateChanged)
        self.browserCustomUserAgentCheckBox.stateChanged.connect(self.handle_browserCustomUserAgent_stateChanged)
        self.spiderExcludeDangerouPathCheckBox.stateChanged.connect(self.handle_spiderExcludeDangerouPath_stateChanged)
        self.framework.subscribe_raft_config_populated(self.configuration_populated)

        self.dataBankTab = DataBankTab.DataBankTab(self.framework, self)
        
        self.dbankFuzzFileAddButton.clicked.connect(self.add_fuzz_file)
        self.dbankFuzzFileDelButton.clicked.connect(self.del_fuzz_file)
        
        self.dbankGenButton.clicked.connect(self.generate_payload)

    def configuration_populated(self):
        self.fill_values()

    def fill_values(self):
        self.bhNetworkBox.setChecked(self.framework.get_raft_config_value('black_hole_network', bool))
        self.checkBoxUseProxy.setChecked(self.framework.get_raft_config_value('use_proxy', bool))
        self.confProxyEdit.setText(self.framework.get_raft_config_value('proxy_host', default_value = 'localhost'))
        self.confProxyPort.setText(self.framework.get_raft_config_value('proxy_port', default_value = '8080'))
        self.confProxyUsername.setText(self.framework.get_raft_config_value('proxy_username'))
        self.confProxyPassword.setText(self.framework.get_raft_config_value('proxy_password'))
        if 'socks5' == self.framework.get_raft_config_value('proxy_type'):
            self.confProxyProxyType.setCurrentIndex(1)
        else:
            self.confProxyProxyType.setCurrentIndex(0)
        self.set_enable_proxy_edits()
        self.fill_browser_edits()
        self.fill_crawler_edits()

    def handle_buttonBox_clicked(self, button):
        role = self.buttonBox.buttonRole(button)
        if role == QDialogButtonBox.AcceptRole:
            self.do_save_config()
            self.dataBankTab.do_save_databank()

    def do_save_config(self):
        self.framework.set_raft_config_value('black_hole_network', bool(self.bhNetworkBox.isChecked()))
        if self.checkBoxUseProxy.isChecked():
            self.framework.set_raft_config_value('proxy_host', self.confProxyEdit.text())
            self.framework.set_raft_config_value('proxy_port', int(self.confProxyPort.text() or '8080'))
            self.framework.set_raft_config_value('proxy_username', self.confProxyUsername.text())
            self.framework.set_raft_config_value('proxy_password', self.confProxyPassword.text())
            if 'http' in self.confProxyProxyType.currentText().lower():
                self.framework.set_raft_config_value('proxy_type', 'http')
            else:
                self.framework.set_raft_config_value('proxy_type', 'socks5')
            self.framework.set_raft_config_value('use_proxy', True)
        else:
            self.framework.set_raft_config_value('use_proxy', False)

        self.save_browser_config()
        self.save_crawler_config()

    def handle_useProxy_stateChanged(self, state):
        self.set_enable_proxy_edits()

    def set_enable_proxy_edits(self):
        if self.checkBoxUseProxy.isChecked():
            self.confProxyEdit.setEnabled(True)            
            self.confProxyPort.setEnabled(True)
            self.confProxyUsername.setEnabled(True)            
            self.confProxyPassword.setEnabled(True)
            self.confProxyProxyType.setEnabled(True)
        else:
            self.confProxyEdit.setEnabled(False)            
            self.confProxyPort.setEnabled(False)
            self.confProxyUsername.setEnabled(False)            
            self.confProxyPassword.setEnabled(False)
            self.confProxyProxyType.setEnabled(False)

    def fill_crawler_edits(self):
        self.fill_spider_edits()

    def save_crawler_config(self):
        self.save_spider_config()

    def value_or_default(self, obj, name, default_value):
        if name in obj:
            return obj[name]
        else:
            return default_value

    def handle_spiderExcludeDangerouPath_stateChanged(self):
        self.spiderDangerousPathEdit.setEnabled(self.spiderExcludeDangerouPathCheckBox.isChecked())

    def handle_browserCustomUserAgent_stateChanged(self):
        self.browserUserAgentEdit.setEnabled(self.browserCustomUserAgentCheckBox.isChecked())

    def fill_spider_edits(self):
        configuration = self.framework.get_raft_config_value('SPIDER', str)
        if configuration:
            obj = json.loads(configuration)
        else:
            obj = {}
        self.spiderSubmitFormsCheckBox.setChecked(bool(self.value_or_default(obj, 'submit_forms', True)))
        self.spiderUseDataBankCheckBox.setChecked(bool(self.value_or_default(obj, 'use_data_bank', True)))
        self.spiderSubmitUsernamePasswordCheckBox.setChecked(bool(self.value_or_default(obj, 'submit_user_name_password', True)))
        self.spiderEvaluateJavascriptCheckBox.setChecked(bool(self.value_or_default(obj, 'evaluate_javascript', True)))
        self.spiderIterateUserAgentsCheckBox.setChecked(bool(self.value_or_default(obj, 'iterate_user_agents', True)))
        self.spiderRetrieveMediaFilesCheckBox.setChecked(bool(self.value_or_default(obj, 'retrieve_media_files', True)))
        self.spiderExcludeDangerouPathCheckBox.setChecked(bool(self.value_or_default(obj, 'exclude_dangerous_paths', False)))
        self.spiderDangerousPathEdit.setText(self.value_or_default(obj, 'dangerous_path', 'delete|remove|destroy'))
        self.spiderMaxLinksEdit.setText(str(self.value_or_default(obj, 'max_links', 8192)))
        self.spiderMaxLinkDepthEdit.setText(str(self.value_or_default(obj, 'max_link_depth', 5)))
        self.spiderMaxChildrenEdit.setText(str(self.value_or_default(obj, 'max_children', 256)))
        self.spiderMaxUniqueParametersEdit.setText(str(self.value_or_default(obj, 'max_unique_parameters', 16)))
        self.spiderRedundantContentLimit.setText(str(self.value_or_default(obj, 'redundant_content_limit', 128)))
        self.spiderRedundantStructureLimit.setText(str(self.value_or_default(obj, 'redundant_structure_limit', 256)))
        self.spiderMediaExtensionsEdit.setText(self.value_or_default(obj, 'media_extensions', 'wmv,mp3,mp4,mpa,gif,jpg,jpeg,png'))

    def save_spider_config(self):
        obj = {}
        obj['submit_forms'] = self.spiderSubmitFormsCheckBox.isChecked()
        obj['use_data_bank'] = self.spiderUseDataBankCheckBox.isChecked()
        obj['submit_user_name_password'] = self.spiderSubmitUsernamePasswordCheckBox.isChecked()
        obj['evaluate_javascript'] = self.spiderEvaluateJavascriptCheckBox.isChecked()
        obj['iterate_user_agents'] = self.spiderIterateUserAgentsCheckBox.isChecked()
        obj['retrieve_media_files'] = self.spiderRetrieveMediaFilesCheckBox.isChecked()
        obj['exclude_dangerous_paths'] = self.spiderExcludeDangerouPathCheckBox.isChecked()
        obj['dangerous_path'] = self.spiderDangerousPathEdit.text()
        obj['max_links'] = int(self.spiderMaxLinksEdit.text())
        obj['max_link_depth'] = int(self.spiderMaxLinkDepthEdit.text())
        obj['max_children'] = int(self.spiderMaxChildrenEdit.text())
        obj['max_unique_parameters'] = int(self.spiderMaxUniqueParametersEdit.text())
        obj['redundant_content_limit'] = int(self.spiderRedundantContentLimit.text())
        obj['redundant_structure_limit'] = int(self.spiderRedundantStructureLimit.text())
        obj['media_extensions'] = self.spiderMediaExtensionsEdit.text()
        configuration = json.dumps(obj)
        self.framework.set_raft_config_value('SPIDER', configuration)

    def fill_browser_edits(self):
        self.browserEnableJavaScriptCheckBox.setChecked(self.framework.get_raft_config_value('browser_javascript_enabled', bool, True))
        self.browserEnableWebStorageCheckBox.setChecked(self.framework.get_raft_config_value('browser_web_storage_enabled', bool, True))
        self.browserEnablePluginsCheckBox.setChecked(self.framework.get_raft_config_value('browser_plugins_enabled', bool, True))
        self.browserEnableJavaCheckBox.setChecked(self.framework.get_raft_config_value('browser_java_enabled', bool, True))
        self.browserAutoLoadImagesCheckBox.setChecked(self.framework.get_raft_config_value('browser_auto_load_images', bool, True))
        self.browserCustomUserAgentCheckBox.setChecked(self.framework.get_raft_config_value('browser_custom_user_agent', bool, False))
        self.browserUserAgentEdit.setText(self.framework.get_raft_config_value('browser_user_agent_value', str, self.framework.useragent()))
    
    def save_browser_config(self):
        self.framework.set_raft_config_value('browser_javascript_enabled', self.browserEnableJavaScriptCheckBox.isChecked())
        self.framework.set_raft_config_value('browser_web_storage_enabled', self.browserEnableWebStorageCheckBox.isChecked())
        self.framework.set_raft_config_value('browser_plugins_enabled', self.browserEnablePluginsCheckBox.isChecked())
        self.framework.set_raft_config_value('browser_java_enabled', self.browserEnableJavaCheckBox.isChecked())
        self.framework.set_raft_config_value('browser_auto_load_images', self.browserAutoLoadImagesCheckBox.isChecked())
        self.framework.set_raft_config_value('browser_custom_user_agent', self.browserCustomUserAgentCheckBox.isChecked())
        self.framework.set_raft_config_value('browser_user_agent_value', self.browserUserAgentEdit.text())
        
    def add_fuzz_file(self):
        
        file = QFileDialog.getOpenFileName(None, "Open file", "")
        shutil.copy(file, self.payloads_dir)
        
        # Refresh the payload list in the interface.
        # pl = Payloads.Payloads()
        self.dataBankTab.fill_payload_combo_box()
        
    def del_fuzz_file(self):
        
        # Gets the current name of the file selected in the combobox
        filename = self.dataBankTab.mainWindow.dbankPayloadsBox.currentText()
        path = self.payloads_dir
        
        message = "Are you sure you want to delete: {0}".format(filename)
        
        response = ConfirmDialog.display_confirm_dialog(self, message)
        
        if response == True:
            os.remove(path + "/" + filename)
            
            self.dataBankTab.fill_payload_combo_box()
                    
            # Clear the items from the textedit
            self.dataBankTab.mainWindow.dbankFuzzValuesEdit.clear()
            
    def write_payload(self, fullpath, start, stop):
        
        step = self.dataBankTab.mainWindow.dbankGenStep.text()
        prepend = self.dataBankTab.mainWindow.dbankGenPre.text()
        postpend = self.dataBankTab.mainWindow.dbankGenPost.text()
        
        
        try:
            f = open(fullpath, "w")
            self.Progress = ProgressDialog()
            for item in range(int(start), int(stop), int(step)):
                f.write(prepend + str(item) + postpend +"\n")   
        
            self.dataBankTab.fill_payload_combo_box()
            
            # Display a message since small payload generation will not show the progress dialog.
            message = "Payload Generated"
            dialog = SimpleDialog(message)
            dialog.exec_()
            
        except Exception as e:
            message = "An error occured:\n%s" % (e)
            dialog = SimpleDialog(message)
            dialog.exec_()
            
            # Remove the file created on error so a blank payload is not listed in the payload list
            os.remove(fullpath)
        
        finally:
            self.Progress.close()
            
            
            
    def generate_payload(self):
        """ Generate a payload file and place it in the payloads directory. Payloads will be one item per line. """
        
        filename = self.dataBankTab.mainWindow.dbankGenPayloadName.text()
        start = self.dataBankTab.mainWindow.dbankGenStart.text()
        stop = self.dataBankTab.mainWindow.dbankGenStop.text()
        step = self.dataBankTab.mainWindow.dbankGenStep.text()
        prepend = self.dataBankTab.mainWindow.dbankGenPre.text()
        postpend = self.dataBankTab.mainWindow.dbankGenPost.text()
        
        if filename == "":
            message = "You didn't specify a filename"
            dialog = SimpleDialog(message)
            dialog.exec_()
            return()
        if start == "":
            message = "You didn't specify a start of the range"
            dialog = SimpleDialog(message)
            dialog.exec_()
            return()
        if stop == "":
            message = "You didn't specify a end of the range"
            dialog = SimpleDialog(message)
            dialog.exec_()
            return()
        
        fullpath = self.payloads_dir + "/" + filename
        
        if os.path.exists(fullpath):
            message = "File already exists. Would you like to overwrite?"
            response = ConfirmDialog.display_confirm_dialog(self, message)
            if response == False:
                return()
            
        self.write_payload(fullpath, start, stop)
            
            
        
    
    
    
