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

from PyQt4.QtCore import Qt, QVariant, QAbstractItemModel, QModelIndex

class GenericDataModel(QAbstractItemModel):

    class _GenericDataNode(object):
        def __init__(self, parent, row, data):
            self.parent = parent
            self.data = data
            self.row = row
            self.children = []

        def findOrAddNode(self, model, data):
            return model.findOrAddDataNode(self, self.children, data)

    def __init__(self, adapter, parent = None):
        QAbstractItemModel.__init__(self, parent)
        self.adapter = adapter
        self.nodes = []

    def findOrAddNode(self, data):
        return self.findOrAddDataNode(None, self.nodes, data)

    def findOrAddDataNode(self, parent, nodes, data):
#        print(parent, nodes, data)
        model = self
        prevNode = None
        foundNode = None
        for index in range(0, len(nodes)):
            if self.adapter.isEqual(data, nodes[index].data):
                foundNode = nodes[index]
                break
            if self.adapter.isLessThan(data, nodes[index].data):
                if (not prevNode) or (prevNode and self.adapter.isLessThan(prevNode.data, data)):
                    if not parent:
                        modelIndex = QModelIndex()
                    else:
                        modelIndex = model.createIndex(index, 0, parent)
                    model.beginInsertRows(modelIndex, index, index)
                    foundNode = self._GenericDataNode(parent, nodes[index].row, data)
                    for i in range(index, len(nodes)):
                        nodes[i].row += 1
                    nodes.insert(index, foundNode)
                    model.endInsertRows()
                    break
            prevNode = nodes[index]

        if not foundNode:
            row = len(nodes)
            index = len(nodes)
            foundNode = self._GenericDataNode(parent, row, data)
            if not parent:
                modelIndex = QModelIndex()
            else:
                modelIndex = model.createIndex(index, 0, parent)
            model.beginInsertRows(modelIndex, index, index)
            nodes.append(foundNode)
            model.endInsertRows()
        return foundNode

    def clearDataNode(self, parent, nodes):
        if not parent:
            modelIndex = QModelIndex()
        else:
            modelIndex = model.createIndex(0, 0, parent)

        for node in nodes:
            if len(node.children)>0:
                clearMapNode(model, node, node.children)

        model.beginRemoveRows(modelIndex, 0, len(nodes)-1)
        nodes = []
        model.endRemoveRows()

    def clearModel(self):
        self.beginResetModel()
        self.nodes = []
        self.endResetModel()

    def index(self, row, column, parent = QModelIndex()):
        if not self.nodes:
            return QModelIndex()
        if not parent.isValid():
            if row >= len(self.nodes):
                return QModelIndex()
            return self.createIndex(row, column, self.nodes[row])
        node = parent.internalPointer()
        if row >= len(node.children):
            return QModelIndex()
        return self.createIndex(row, column, node.children[row])

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
#        print(node)
        if node.parent is None:
            return QModelIndex()
        else:
            return self.createIndex(node.parent.row, 0, node.parent)

    def rowCount(self, parent = QModelIndex()):
        if not parent.isValid():
            return len(self.nodes)
        node = parent.internalPointer()
        if not node:
            return 0
        return len(node.children)

    def columnCount(self, parent):
        return self.adapter.columnCount()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.adapter.columnName(section)
        return QVariant()

    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        node = index.internalPointer()
        if role == Qt.DisplayRole:
            return QVariant(self.adapter.getData(node.data, index.column()))
        return QVariant()
            
