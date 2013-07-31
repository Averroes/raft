#
# This module supports the data model for the responses data for TreeViews
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

from PyQt4.QtCore import Qt, QVariant, QAbstractItemModel, QModelIndex, QAbstractTableModel
from core.data.DataTableDataModel import DataTableDataModel
from core.database.constants import ResponsesTable

class ResponsesDataModel(DataTableDataModel):

    ITEM_DEFINITION = (
            ('#', ResponsesTable.ID),
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
            ('Request Hash', ResponsesTable.REQ_DATA_HASHVAL),
            ('Response Hash', ResponsesTable.RES_DATA_HASHVAL),
            )

    def __init__(self, framework, parent = None):
        DataTableDataModel.__init__(self, framework, ResponsesDataModel.ITEM_DEFINITION, parent)
