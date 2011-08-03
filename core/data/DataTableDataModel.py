#
# This module supports the data model for the data for tables
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
from collections import deque

class DataTableDataModel(QAbstractTableModel):
    def __init__(self, framework, item_definition, parent = None):
        QAbstractItemModel.__init__(self, parent)
        self.framework = framework
        self.rows = deque()
        self.item_definition = item_definition

        self.column_offset = []
        self.db_offset = {}
        self.column_count = 0
        for item in self.item_definition:
            self.column_offset.append(item[1])
            self.db_offset[item[1]] = self.column_count
            self.column_count += 1

    def translate_offset(self, db_offset):
        return self.db_offset[db_offset]

    def pop_data(self):
        current_size = len(self.rows)
        if 0 == current_size:
            return None
        start = current_size - 1
        end = start
        modelIndex = QModelIndex()
        self.beginRemoveRows(modelIndex, start, end)
        data = self.rows.pop()
        self.endRemoveRows()
        return data

    def popleft_data(self):
        current_size = len(self.rows)
        if 0 == current_size:
            return None
        modelIndex = QModelIndex()
        self.beginRemoveRows(modelIndex, 0, 0)
        data = self.rows.popleft()
        self.endRemoveRows()
        return data

    def append_data(self, new_rows):
        size = len(new_rows)
        if 0 == size:
            return
        modelIndex = QModelIndex()
        current_size = len(self.rows)
        start = current_size
        end = current_size + size - 1
        self.beginInsertRows(modelIndex, start, end)
        for row in new_rows:
            self.rows.append(row)
        self.endInsertRows()

    def appendleft_data(self, new_rows):
        size = len(new_rows)
        if 0 == size:
            return
        modelIndex = QModelIndex()
        self.beginInsertRows(modelIndex, 0, size - 1)
        for row in new_rows:
            self.rows.appendleft(row)
        self.endInsertRows()

    def clearModel(self):
        self.beginResetModel()
        for row in self.rows:
            del(row)
        self.rows = deque()
        self.endResetModel()

    def columnCount(self, parent = QModelIndex()):
        if parent.isValid():
            return 0
        return self.column_count

    def columnName(self, parent):
        if parent.isValid():
            return 0
        return self.column_count

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.item_definition[section][0])
        return QVariant()

    def rowCount(self, parent = QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.rows)

    def hasChildren(self, parent = QModelIndex()):
        if parent.isValid():
            return False
        return True

    def parent(self, index):
        return QModelIndex()
        
    def data(self, index, role = Qt.DisplayRole):
        try:
            if not index.isValid():
                return QVariant()
            if role == Qt.DisplayRole:
                row = index.row()
                column = self.column_offset[index.column()]
                data = self.rows[row][column]
                return QVariant(data)
            return QVariant()
        except IndexError:
            return QVariant()
