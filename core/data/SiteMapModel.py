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

def findOrAddSiteMapNode(model, parent, nodes, text):
    prevNode = None
    foundNode = None
    for index in range(0, len(nodes)):
        # keep in order
        if text == nodes[index].text:
            foundNode = nodes[index]
            break
        if text < nodes[index].text:
            if (not prevNode) or (prevNode and prevNode.text < text):
                if not parent:
                    modelIndex = QModelIndex()
                else:
                    modelIndex = model.createIndex(index, 0, parent)
                model.beginInsertRows(modelIndex, index, index)
                foundNode = SiteMapNode(parent, nodes[index].row, text)
                for i in range(index, len(nodes)):
                    nodes[i].row += 1
                nodes.insert(index, foundNode)
                model.endInsertRows()
                break
        prevNode = nodes[index]

    if not foundNode:
        row = len(nodes)
        index = len(nodes)
        foundNode = SiteMapNode(parent, row, text)
        if not parent:
            modelIndex = QModelIndex()
        else:
            modelIndex = model.createIndex(index, 0, parent)
        model.beginInsertRows(modelIndex, index, index)
        nodes.append(foundNode)
        model.endInsertRows()
    return foundNode

def clearMapNode(model, parent, nodes):
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

class SiteMapNode(object):
    def __init__(self, parent, row, text):
        self.parent = parent
        self.text = text
        self.Id = None
        self.url = None
        self.row = row
        self.children = []

    def findOrAddNode(self, model, text):
        return findOrAddSiteMapNode(model, self, self.children, text)

    def setResponseId(self, Id, url):
        self.Id = Id
        self.url = url

class SiteMapModel(QAbstractItemModel):
    def __init__(self, framework, parent = None):
        QAbstractItemModel.__init__(self, parent)
        self.framework = framework
        self.nodes = []

    def findOrAddNode(self, text):
        return findOrAddSiteMapNode(self, None, self.nodes, text)

    def clearModel(self):
#        clearMapNode(self, None, self.nodes)
        self.beginResetModel()
        self.nodes = []
        self.endResetModel()

    def index(self, row, column, parent):
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
        if node.parent is None:
            return QModelIndex()
        else:
            return self.createIndex(node.parent.row, 0, node.parent)

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self.nodes)
        node = parent.internalPointer()
        if not node:
            return 0
        return len(node.children)

    def columnCount(self, parent):
        return 1

    def headerData(self, section, orientation, role):
        if 0 == section and orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return 'Name' # QVariant('Name')
        return None # QVariant()
        
    def data(self, index, role):
        if not index.isValid():
            return None # QVariant()
        node = index.internalPointer()
        if role == Qt.DisplayRole:
            return node.text # QVariant(node.text)
        return None # QVariant()

