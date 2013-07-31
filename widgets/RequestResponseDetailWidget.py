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

from core.database.constants import ResponsesTable

class RequestResponseDetailWidget(QObject):
    def __init__(self, framework, widget, responseId, parent):
        QObject.__init__(self, parent)
        self.framework = framework
        self.fill_widget = widget
        self.responseId = responseId

        self.itemDefinition = (
            ('ID #', ResponsesTable.ID),
            ('URL', ResponsesTable.URL),
            ('Method', ResponsesTable.REQ_METHOD),
            ('Host', ResponsesTable.REQ_HOST),
            ('Request Date', ResponsesTable.REQDATE),
            ('HTTP Status', ResponsesTable.STATUS),
            ('Content Type', ResponsesTable.RES_CONTENT_TYPE),
            ('Content Length', ResponsesTable.RES_LENGTH),
            ('Host IP', ResponsesTable.HOST_IP),
            ('Confirmed', ResponsesTable.CONFIRMED),
            ('Origin', ResponsesTable.DATA_ORIGIN),
            ('Elapsed Request Time', ResponsesTable.REQTIME),
            ('Request Data Hash', ResponsesTable.REQ_DATA_HASHVAL),
            ('Response Data Hash', ResponsesTable.RES_DATA_HASHVAL),
            )

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.fill_detail(self.responseId)

    def db_detach(self):
        if self.Data:
            self.close_cursor()
            self.Data = None

    def close_cursor(self):
        if self.cursor:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def close(self):
        self.close_cursor()
        self.Data = None

    def fill_detail(self, responseId):

        row = self.Data.read_responses_by_id(self.cursor, responseId)
        if not row:
            return

        responseItems = [m or '' for m in list(row)]

        self.vbox = QVBoxLayout(self.fill_widget)
        
        for name, index in self.itemDefinition:
            value = str(responseItems[index])
            if index == ResponsesTable.CONFIRMED:
                if value and value.lower() in ['y', '1']:
                    value = 'Yes'
                else:
                    value = 'No'
            hbox = QHBoxLayout()
            labelName = QLabel(self.fill_widget)
            labelValue = QLabel(self.fill_widget)
            labelName.setText(name + ': ')
            labelValue.setText(value)
            hbox.addWidget(labelName)
            hbox.addWidget(labelValue)
            hbox.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
            self.vbox.addItem(hbox)
