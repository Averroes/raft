#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#         Nathan Hamiel
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

import time
from urllib2 import urlparse

from PyQt4.QtCore import Qt, SIGNAL, QObject, QModelIndex
from PyQt4.QtGui import *

from cStringIO import StringIO

from actions import interface
from core.database.constants import ResponsesTable

from lib.parsers.raftparse import ParseAdapter
from core.data.RaftDbCapture import RaftDbCapture
import bz2

class ResponsesContextMenuWidget(QObject):
    def __init__(self, framework, dataModel, treeView, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework
        self.dataModel = dataModel
        self.treeView = treeView

        self.selectionChanged_callback = None
        self.currentChanged_callback = None

        self.treeView.setSelectionMode(self.treeView.ExtendedSelection)
        self.treeViewSelectionModel = QItemSelectionModel(self.dataModel)
        self.treeView.setSelectionModel(self.treeViewSelectionModel)
        self.treeViewSelectionModel.selectionChanged.connect(self.handle_selectionChanged)
        self.treeViewSelectionModel.currentChanged.connect(self.handle_currentChanged)

        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.treeView, SIGNAL("customContextMenuRequested(const QPoint&)"), self.responses_data_context_menu)
        self.menu = QMenu(self.treeView)

        self.sendToRequesterAction = action = QAction("Send to Requester", self)
        action.triggered.connect(self.send_response_data_to_requester)
        self.menu.addAction(action)

        action = QAction("Send to Differ", self)
        action.triggered.connect(self.send_response_data_to_differ)
        self.menu.addAction(action)

        action = QAction("Send to Web Fuzzer", self)
        action.triggered.connect(self.send_response_data_to_web_fuzzer)
        self.menu.addAction(action)

        action = QAction("Send to DOM Fuzzer", self)
        action.triggered.connect(self.send_response_data_to_dom_fuzzer)
        self.menu.addAction(action)

        action = QAction("Send to Spider", self)
        action.triggered.connect(self.send_response_data_to_spider)
        self.menu.addAction(action)

        action = QAction("Send to Sequence Builder", self)
        action.triggered.connect(self.send_response_data_to_sequence_builder)
        self.menu.addAction(action)

        self.copyUrlAction = action = QAction("Copy URL", self)
        action.triggered.connect(self.data_tree_copy_url)
        self.menu.addAction(action)

        self.testerAction = QAction("Testing...", self)
        self.testerSubMenu = QMenu(self.treeView)
        self.testerAction.setMenu(self.testerSubMenu)
        self.menu.addAction(self.testerAction)
        action = QAction("Send to CSRF Tester", self)
        action.triggered.connect(self.send_response_data_to_csrf_tester)
        self.testerSubMenu.addAction(action)
        action = QAction("Send to Click Jacking Tester", self)
        action.triggered.connect(self.send_response_data_to_click_jacking_tester)
        self.testerSubMenu.addAction(action)

        self.hideAction = QAction("Hide...", self)
        self.hideSubMenu = QMenu(self.treeView)
        self.hideAction.setMenu(self.hideSubMenu)
        self.menu.addAction(self.hideAction)
        self.hideSubMenu.addAction(self.make_data_tree_hide_item_action("Hide this URL", ResponsesTable.URL))
        self.hideSubMenu.addAction(self.make_data_tree_hide_item_action("Hide this Method", ResponsesTable.REQ_METHOD))
        self.hideSubMenu.addAction(self.make_data_tree_hide_item_action("Hide this Host", ResponsesTable.REQ_HOST))
        self.hideSubMenu.addAction(self.make_data_tree_hide_item_action("Hide this Status", ResponsesTable.STATUS))
        self.hideSubMenu.addAction(self.make_data_tree_hide_item_action("Hide this Content Type", ResponsesTable.RES_CONTENT_TYPE))
        self.hideSubMenu.addAction(self.make_data_tree_hide_item_action("Hide this Host IP", ResponsesTable.HOST_IP))
        self.hideSubMenu.addAction(self.make_data_tree_hide_item_action("Hide this Confirmed", ResponsesTable.CONFIRMED))
        self.hideSubMenu.addAction(self.make_data_tree_hide_item_action("Hide this Origin", ResponsesTable.DATA_ORIGIN))
        self.hideSubMenu.addAction(self.make_data_tree_hide_item_action("Hide this Request Data Hash", ResponsesTable.REQ_DATA_HASHVAL))
        self.hideSubMenu.addAction(self.make_data_tree_hide_item_action("Hide this Response Data Hash", ResponsesTable.RES_DATA_HASHVAL))

        self.showAction = QAction("Show...", self)
        self.showSubMenu = QMenu(self.treeView)
        self.showAction.setMenu(self.showSubMenu)
        self.menu.addAction(self.showAction)
        self.showSubMenu.addAction(self.make_data_tree_show_item_action("Show only this URL", ResponsesTable.URL))
        self.showSubMenu.addAction(self.make_data_tree_show_item_action("Show only this Method", ResponsesTable.REQ_METHOD))
        self.showSubMenu.addAction(self.make_data_tree_show_item_action("Show only this Host", ResponsesTable.REQ_HOST))
        self.showSubMenu.addAction(self.make_data_tree_show_item_action("Show only this Status", ResponsesTable.STATUS))
        self.showSubMenu.addAction(self.make_data_tree_show_item_action("Show only this Content Type", ResponsesTable.RES_CONTENT_TYPE))
        self.showSubMenu.addAction(self.make_data_tree_show_item_action("Show only this Host IP", ResponsesTable.HOST_IP))
        self.showSubMenu.addAction(self.make_data_tree_show_item_action("Show only this Confirmed", ResponsesTable.CONFIRMED))
        self.showSubMenu.addAction(self.make_data_tree_show_item_action("Show only this Origin", ResponsesTable.DATA_ORIGIN))
        self.showSubMenu.addAction(self.make_data_tree_show_item_action("Show only this Request Data Hash", ResponsesTable.REQ_DATA_HASHVAL))
        self.showSubMenu.addAction(self.make_data_tree_show_item_action("Show only this Response Data Hash", ResponsesTable.RES_DATA_HASHVAL))

        responsesDataTreeShowAction = QAction("Show In Scope", self)
        responsesDataTreeShowAction.triggered.connect(self.data_tree_show_in_scope)
        self.menu.addAction(responsesDataTreeShowAction)

        responsesDataTreeShowAction = QAction("Show All", self)
        responsesDataTreeShowAction.triggered.connect(self.data_tree_show_all)
        self.menu.addAction(responsesDataTreeShowAction)

        self.saveResponseToFileAction = QAction("Save Response to File", self)
        self.saveResponseToFileAction.triggered.connect(self.save_response_to_file)
        self.menu.addAction(self.saveResponseToFileAction)

        action = QAction("Export to RAFT Capture", self)
        action.triggered.connect(self.export_to_raft_capture)
        self.menu.addAction(action)

        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def set_selectionChanged_callback(self, callback):
        self.selectionChanged_callback = callback

    def set_currentChanged_callback(self, callback):
        self.currentChanged_callback = callback

    def handle_selectionChanged(self, index):
        if self.selectionChanged_callback is not None:
            self.selectionChanged_callback(index)

    def handle_currentChanged(self, index):
        if self.currentChanged_callback is not None:
            self.currentChanged_callback(index)

    def export_to_raft_capture(self):
        # TODO: consider implementing a tasklet if this is the entire DB being exported
        filename = 'RaftExport-%s' % int(time.time())
        file = QFileDialog.getSaveFileName(None, "Save to file", filename, "XML File (*.xml);;BZ2 XML File (*.xml.bz2)")
        if file:
            adapter = ParseAdapter()
            # TODO: refactor
            filename = str(file)
            if filename.endswith('.xml.bz2'):
                filename = filename.replace('.xml.bz2.xml.bz2', '.xml.bz2')
                fh = bz2.BZ2File(filename, 'w')
            elif filename.endswith('.xml'):
                filename = filename.replace('.xml.xml', '.xml')
                fh = open(filename, 'wb')
            else:
                raise Exception('unhandled file type: %s' % (filename))
            Data = self.framework.getDB()
            cursor = Data.allocate_thread_cursor()
            try:
                fh.write('<raft version="1.0">\n')
                for index in self.treeViewSelectionModel.selectedRows():
                    Id = interface.index_to_id(self.dataModel, index)
                    if Id:
                        capture = RaftDbCapture(self.framework, Data, cursor, Id)
                        fh.write(adapter.format_as_xml(capture))
                fh.write('</raft>')
                fh.close()
            finally:
                cursor.close()
                Data.release_thread_cursor(cursor)
                Data, cursor = None, None

    def save_response_to_file(self):
        index = self.treeView.currentIndex()
        Id = interface.index_to_id(self.dataModel, index)
        curUrl = interface.index_to_url(self.dataModel, index)
        if Id and curUrl:
            splitted = urlparse.urlsplit(curUrl)
            pos = splitted.path.rindex('/')
            filename = ''
            if pos > -1:
                filename = splitted.path[pos+1:]
            
            file = QFileDialog.getSaveFileName(None, "Save to file", filename, "")
            if file:
                filename = str(file)
                fh = open(filename, 'wb')
                try:
                    rr = self.framework.get_request_response(Id)
                    fh.write(rr.responseBody)
                finally:
                    fh.close()

    def send_response_data_to_requester(self):
        id_list = []
        for index in self.treeViewSelectionModel.selectedRows():
            Id = interface.index_to_id(self.dataModel, index)
            if Id:
                id_list.append(Id)

        if 1 == len(id_list):
            self.framework.send_response_id_to_requester(id_list[0])

    def responses_data_context_menu(self, point):
        """ Display the context menu for the TreeView """

        if len(self.treeViewSelectionModel.selectedRows()) > 1:
            self.copyUrlAction.setText('Copy URLs')
            self.sendToRequesterAction.setText('Send to Bulk Requester')
            self.saveResponseToFileAction.setEnabled(False)
        else:
            self.copyUrlAction.setText('Copy URL')
            self.sendToRequesterAction.setText('Send to Requester')
            self.saveResponseToFileAction.setEnabled(True)

        self.menu.exec_(self.treeView.mapToGlobal(point))

    def send_response_data_to_differ(self):
        index = self.treeView.currentIndex()
        if len(self.treeViewSelectionModel.selectedRows()) > 1:
            id_list = []
            for index in self.treeViewSelectionModel.selectedRows():
                Id = interface.index_to_id(self.dataModel, index)
                id_list.append(str(Id))
            self.framework.send_response_list_to_differ(id_list)
        else:
            Id = interface.index_to_id(self.dataModel, index)
            if Id:
                self.framework.send_response_id_to_differ(Id)

    def send_response_data_to_web_fuzzer(self):
        index = self.treeView.currentIndex()
        Id = interface.index_to_id(self.dataModel, index)
        if Id:
            self.framework.send_response_id_to_webfuzzer(Id)

    def send_response_data_to_dom_fuzzer(self):
        index = self.treeView.currentIndex()
        if len(self.treeViewSelectionModel.selectedRows()) > 1:
            id_list = []
            for index in self.treeViewSelectionModel.selectedRows():
                Id = interface.index_to_id(self.dataModel, index)
                id_list.append(str(Id))
            self.framework.send_response_list_to_domfuzzer(id_list)
        else:
            Id = interface.index_to_id(self.dataModel, index)
            if Id:
                self.framework.send_response_id_to_domfuzzer(Id)

    def send_response_data_to_spider(self):
        index = self.treeView.currentIndex()
        if len(self.treeViewSelectionModel.selectedRows()) > 1:
            id_list = []
            for index in self.treeViewSelectionModel.selectedRows():
                Id = interface.index_to_id(self.dataModel, index)
                id_list.append(str(Id))
            self.framework.send_response_list_to_spider(id_list)
        else:
            Id = interface.index_to_id(self.dataModel, index)
            if Id:
                self.framework.send_response_id_to_spider(Id)

    def send_response_data_to_sequence_builder(self):
        index = self.treeView.currentIndex()
        Id = interface.index_to_id(self.dataModel, index)
        if Id:
            self.framework.send_response_id_to_sequence_builder(Id)

    def data_tree_copy_url(self):
        url_list = []
        for index in self.treeViewSelectionModel.selectedRows():
            curUrl = interface.index_to_url(self.dataModel, index)
            if curUrl:
                url_list.append('%s' % (str(curUrl)))

        QApplication.clipboard().setText('\n'.join(url_list))

    def make_data_tree_hide_item_action(self, msg, index):
        treeViewHideAction = QAction(msg, self)
        treeViewHideAction.triggered.connect(lambda x: self.data_tree_hide_item(index))
        return treeViewHideAction

    def data_tree_hide_item(self, offset):
        column = self.dataModel.translate_offset(offset)
        index = self.treeView.currentIndex()
        index = self.dataModel.index(index.row(), column)
        if index.isValid():
            value = str(self.dataModel.data(index).toString())
            for i in range(0, self.dataModel.rowCount()):
                itemIndex = self.dataModel.index(i, column)
                data = str(self.dataModel.data(itemIndex).toString())
                if data == value:
                    self.treeView.setRowHidden(i, QModelIndex(), True)

    def make_data_tree_show_item_action(self, msg, index):
        treeViewShowAction = QAction(msg, self)
        treeViewShowAction.triggered.connect(lambda x: self.data_tree_show_item(index))
        return treeViewShowAction

    def data_tree_show_item(self, offset):
        column = self.dataModel.translate_offset(offset)
        index = self.treeView.currentIndex()
        index = self.dataModel.index(index.row(), column)
        if index.isValid():
            value = str(self.dataModel.data(index).toString())
            for i in range(0, self.dataModel.rowCount()):
                itemIndex = self.dataModel.index(i, column)
                data = str(self.dataModel.data(itemIndex).toString())
                if data != value:
                    self.treeView.setRowHidden(i, QModelIndex(), True)

    def data_tree_show_in_scope(self):
        scopeController = self.framework.getScopeController()
        urlColumn = self.dataModel.translate_offset(ResponsesTable.URL)
        for i in range(0, self.dataModel.rowCount()):
            itemIndex = self.dataModel.index(i, urlColumn)
            url = str(self.dataModel.data(itemIndex).toString())
            if scopeController.isUrlInScope(url, url):
                self.treeView.setRowHidden(i, QModelIndex(), False)
            else:
                self.treeView.setRowHidden(i, QModelIndex(), True)

    def data_tree_show_all(self):
        for i in range(0, self.dataModel.rowCount()):
            self.treeView.setRowHidden(i, QModelIndex(), False)

    def send_response_data_to_csrf_tester(self):
        index = self.treeView.currentIndex()
        Id = interface.index_to_id(self.dataModel, index)
        if Id:
            self.framework.send_to_tester_csrf(Id)

    def send_response_data_to_click_jacking_tester(self):
        index = self.treeView.currentIndex()
        Id = interface.index_to_id(self.dataModel, index)
        if Id:
            self.framework.send_to_tester_click_jacking(Id)

