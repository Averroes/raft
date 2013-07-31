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
from PyQt4.QtCore import Qt, QObject, SIGNAL, QThread, QTimer, QMutex
from PyQt4.QtGui import *

class VulnerabilitiesTab(QObject):
    def __init__(self, framework, mainWindow):
        QObject.__init__(self, mainWindow)
        self.framework = framework
        self.mainWindow = mainWindow
        self.treeWidget = mainWindow.treeWidgetVulnerabilities

        self.treeWidget.activated.connect(self.do_populate_vulnerability)
        self.treeWidget.clicked.connect(self.do_populate_vulnerability)
#        self.treeWidget.itemSelectionChanged.connect()
        self.mainWindow.pushButtonVulnerabilitySave.clicked.connect(self.do_save_vulnerability)
        self.mainWindow.pushButtonVulnerabilityReset.clicked.connect(self.do_reset_vulnerability_entry)
        self.mainWindow.pushButtonVulnerabilityAddParameter.clicked.connect(self.do_add_vuln_parameter)
        self.mainWindow.pushButtonVulnerabilitySaveParameter.clicked.connect(self.do_save_vuln_parameter)

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.fill_vulnerabilities()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def fill_vulnerabilities(self):
        self.treeWidget.clearSelection()
        self.treeWidget.clear()
        for row in self.Data.get_all_vulnerabilities(self.cursor):
            vuln = [str(m) or '' for m in row]
            item = QTreeWidgetItem(vuln)

            parameters = self.Data.get_vulnerability_parameters(self.cursor, vuln[0])
            self.parameters = []
            if parameters:
                for row2 in parameters:
                    param = [str(m) or '' for m in row2]
                    self.parameters.append(param)
                    child = QTreeWidgetItem(item, param)

            self.treeWidget.addTopLevelItem(item)

        self.do_reset_vulnerability_entry()
        
    def do_save_vulnerability(self):
        if self.currentId:
            insertlist = [
                str(self.mainWindow.editVulnerabilityHostname.text()),
                str(self.mainWindow.editVulnerabilityPort.text()),
                str(self.mainWindow.editVulnerabilityCategory.text()),
                str(self.mainWindow.comboBoxVulnerbalitySeverity.currentText()),
                str(self.mainWindow.editVulnerabilityUrl.text()),
                str(self.mainWindow.cbVulnerabilityFalsePositive.isChecked()),
                str(self.mainWindow.editVulnerabilityRemediation.toPlainText()),
                self.currentId
                ]
            self.Data.update_vulnerability(self.cursor, insertlist)

            for param in self.parameters:
                self.Data.upsert_vulnerability_parameter(self.cursor, self.currentId, param)

        else:
            insertlist = [
                None,
                str(self.mainWindow.editVulnerabilityHostname.text()),
                str(self.mainWindow.editVulnerabilityPort.text()),
                str(self.mainWindow.editVulnerabilityCategory.text()),
                str(self.mainWindow.comboBoxVulnerbalitySeverity.currentText()),
                str(self.mainWindow.editVulnerabilityUrl.text()),
                str(self.mainWindow.cbVulnerabilityFalsePositive.isChecked()),
                str(self.mainWindow.editVulnerabilityRemediation.toPlainText()),
                ]
            self.currentId = self.Data.insert_new_vulnerability(self.cursor, insertlist)

        self.fill_vulnerabilities()

    def do_populate_vulnerability(self):
        item = self.treeWidget.currentItem()
        if not item:
            self.do_reset_vulnerability_entry()
            return

        parent = item.parent()
        parameterNum = None
        if parent:
            # parameter
            vulnerabilityId = str(parent.text(0))
            parameterNum = str(item.text(0))
        else:
            vulnerabilityId = str(item.text(0))
            self.reset_parameter_entry()

        row = self.Data.get_vulnerability_by_id(self.cursor, vulnerabilityId)
        if not row:
            self.do_reset_vulnerability_entry()
            return
        vuln = [str(m) or '' for m in row]
        self.currentId = vuln[0]
        self.mainWindow.editVulnerabilityHostname.setText(vuln[1])
        self.mainWindow.editVulnerabilityPort.setText(vuln[2])
        self.mainWindow.editVulnerabilityCategory.setText(vuln[3])
        self.mainWindow.comboBoxVulnerbalitySeverity.setCurrentIndex(self.mainWindow.comboBoxVulnerbalitySeverity.findText(vuln[4]))
        self.mainWindow.editVulnerabilityUrl.setText(vuln[5])
        checked = False
        if vuln[6] in ('True', 'Yes'):
            checked = True
        self.mainWindow.cbVulnerabilityFalsePositive.setChecked(checked)
        self.mainWindow.editVulnerabilityRemediation.setPlainText(vuln[7])

        if parameterNum:
            self.do_populate_parameter(vulnerabilityId, parameterNum)

        # self.parameters = []
        # rows = self.Data.get_vulnerability_parameters(vuln[0])
        # if rows:
        #     for row in rows:
        #         param = [str(m) or '' for m in row]
        #         self.parameters.append(param)
        #         self.add_parameter_tab(param)

    def do_reset_vulnerability_entry(self):
        self.currentId = ''
        self.mainWindow.editVulnerabilityHostname.setText('')
        self.mainWindow.editVulnerabilityPort.setText('')
        self.mainWindow.editVulnerabilityCategory.setText('')
        self.mainWindow.comboBoxVulnerbalitySeverity.setCurrentIndex(0)
        self.mainWindow.editVulnerabilityUrl.setText('')
        self.mainWindow.cbVulnerabilityFalsePositive.setChecked(False)
        self.mainWindow.editVulnerabilityRemediation.setPlainText('')
        self.reset_parameter_entry()

    def do_delete_vulnerability(self):
        if not self.currentId:
            return
        pass

    def do_populate_parameter(self, vulnerabilityId, paramNum):
        # row = self.Data.get_vulnerability_parameter_by_num(vulnerabilityId, paramNum)
        # if not row:
        #     self.reset_parameter_entry()
        #     return
        # param = [str(m) or '' for m in row]
        self.currentParamNum = paramNum
        param = None
        for p in self.parameters:
            if p[0] == paramNum:
                param = p
                break
        if not param:
            self.reset_parameter_entry()
            return
        self.mainWindow.editVulnerabilityParameterName.setText(param[1])
        self.mainWindow.editVulnerabilityParameterPayload.setText(param[2])
        self.mainWindow.editVulnerabilityParameterExample.setText(param[3])

    def reset_parameter_entry(self):
        self.currentParamNum = None
        self.mainWindow.editVulnerabilityParameterName.setText('')
        self.mainWindow.editVulnerabilityParameterPayload.setText('')
        self.mainWindow.editVulnerabilityParameterExample.setText('')

    def do_save_vuln_parameter(self):
        if not self.currentParamNum:
            self.do_add_vuln_parameter()
        else:
            param = None
            for p in self.parameters:
                if p[0] == self.currentParamNum:
                    param = p
                    break
            if not param:
                return
            param = [
                str(self.currentParamNum),
                str(self.mainWindow.editVulnerabilityParameterName.text()),
                str(self.mainWindow.editVulnerabilityParameterPayload.text()),
                str(self.mainWindow.editVulnerabilityParameterExample.text()),
                ]

            item = self.treeWidget.currentItem()
            item.setData(1, Qt.DisplayRole, param[1])
            item.setData(2, Qt.DisplayRole, param[2])
            item.setData(3, Qt.DisplayRole, param[3])

    def do_add_vuln_parameter(self):

        item = self.treeWidget.currentItem()
        if not item:
            return

        nextNum = 1
        if len(self.parameters) > 0:
            nextNum = int(self.parameters[-1][0])+1
        newParam = [
                str(nextNum),
                str(self.mainWindow.editVulnerabilityParameterName.text()),
                str(self.mainWindow.editVulnerabilityParameterPayload.text()),
                str(self.mainWindow.editVulnerabilityParameterExample.text()),
                ]
        self.parameters.append(newParam)

        item = self.treeWidget.currentItem()
        parent = item.parent()
        if parent:
            item = parent
        item.addChild(QTreeWidgetItem(newParam))
        self.currentParamNum = nextNum
