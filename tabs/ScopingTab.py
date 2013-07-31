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

from PyQt4.QtCore import Qt, QObject, SIGNAL, QUrl
from PyQt4.QtGui import *
import json

class ScopingTab(QObject):
    def __init__(self, framework, mainWindow):
        QObject.__init__(self, mainWindow)
        self.framework = framework
        self.mainWindow = mainWindow

        self.mainWindow.scopingSaveButton.clicked.connect(self.handle_saveButton_clicked)

        self.configurationObject = {}
        self.mainWindow.scopingSaveButton.setEnabled(False)
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)
        self.framework.subscribe_raft_config_updated(self.raft_config_updated)

    def db_attach(self):
        self.fill_edit_boxes()
        self.mainWindow.scopingSaveButton.setEnabled(True)

    def db_detach(self):
        self.mainWindow.scopingSaveButton.setEnabled(False)

    def raft_config_updated(self, config_name, config_value):
        if 'SCOPING' == config_name:
            # TODO: account for unsaved changes?
            self.fill_edit_boxes()

    def fill_edit_boxes(self):
        configuration = self.framework.get_raft_config_value('SCOPING', str)
        if configuration:
            self.configurationObject = json.loads(configuration)
            self.mainWindow.scopingUrlPathsIncludeEdit.setPlainText(self.configurationObject.get('UrlPathsInclude') or '')
            self.mainWindow.scopingUrlPathsExcludeEdit.setPlainText(self.configurationObject.get('UrlPathsExclude') or '')
            self.mainWindow.scopingHostnamesIncludeEdit.setPlainText(self.configurationObject.get('HostnamesInclude') or '')
            self.mainWindow.scopingHostnamesExcludeEdit.setPlainText(self.configurationObject.get('HostnamesExclude') or '')
            self.mainWindow.scopingIPAddressesIncludeEdit.setPlainText(self.configurationObject.get('IPAddressesInclude') or '')
            self.mainWindow.scopingIPAddressesExcludeEdit.setPlainText(self.configurationObject.get('IPAddressesExclude') or '')
        
    def handle_saveButton_clicked(self):
        self.configurationObject['UrlPathsInclude'] = str(self.mainWindow.scopingUrlPathsIncludeEdit.toPlainText())
        self.configurationObject['UrlPathsExclude'] = str(self.mainWindow.scopingUrlPathsExcludeEdit.toPlainText())
        self.configurationObject['HostnamesInclude'] = str(self.mainWindow.scopingHostnamesIncludeEdit.toPlainText())
        self.configurationObject['HostnamesExclude'] = str(self.mainWindow.scopingHostnamesExcludeEdit.toPlainText())
        self.configurationObject['IPAddressesInclude'] = str(self.mainWindow.scopingIPAddressesIncludeEdit.toPlainText())
        self.configurationObject['IPAddressesExclude'] = str(self.mainWindow.scopingIPAddressesExcludeEdit.toPlainText())
        configuration = json.dumps(self.configurationObject)
        self.framework.set_raft_config_value('SCOPING', configuration)
        
