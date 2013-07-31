#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2013 RAFT Team
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
from PyQt4.QtCore import Qt, QObject, SIGNAL, QDateTime
from PyQt4.QtGui import QTableWidget, QTableWidgetItem, QHeaderView

class LogTab(QObject):
    def __init__(self, framework, mainWindow):
        QObject.__init__(self, mainWindow)
        self.framework = framework
        self.mainWindow = mainWindow

        self.tableWidget = self.mainWindow.logTableWidget
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(['Date', 'Type', 'Message'])
        self.tableWidget.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)

        self.mainWindow.logTableClearLogButton.clicked.connect(self.handle_logTableClearLogButton_clicked)

        self.framework.subscribe_log_events(self.log_message)

    def log_message(self, message_type, message):

        # TODO: set alignment
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)
        self.tableWidget.setItem(row, 0, QTableWidgetItem(QDateTime.currentDateTime().toString('yyyy.MM.dd hh:mm:ss.zzz')))
        self.tableWidget.setItem(row, 1, QTableWidgetItem(message_type))
        self.tableWidget.setItem(row, 2, QTableWidgetItem(message))
        self.tableWidget.resizeRowToContents(row)

    def handle_logTableClearLogButton_clicked(self):
        # TODO: is clearContents needed?
        # self.tableWidget.clearContents()
        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow(0)

