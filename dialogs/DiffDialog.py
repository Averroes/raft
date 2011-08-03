#
# Diff dialog to show differences in response content
#
# Authors: 
#          Nathan Hamiel
#          Gregory Fleischer (gfleischer@gmail.com)
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

import difflib

from PyQt4.QtCore import (Qt, SIGNAL, QObject)
from PyQt4.QtGui import *

from ui import DiffDialog
from dialogs.ProgressDialog import ProgressDialog
from dialogs.DiffCustomDialog import DiffCustomDialog
from core.database.constants import ResponsesTable

class DiffDialog(QDialog, DiffDialog.Ui_DiffDialog):
    """ Visual dialog that allows for the diffing of two responses """
    
    def __init__(self, framework, parent=None):
        super(DiffDialog, self).__init__(parent)
        self.setupUi(self)

        self.framework = framework
        self.Progress = ProgressDialog()
        self.framework.subscribe_add_differ_response_id(self.differ_add_response_id)

        # Create progress dialog
        self.customButton.clicked.connect(self.custom_diff)
        self.leftTree.itemSelectionChanged.connect(self.diff_items)
        self.rightTree.itemSelectionChanged.connect(self.diff_items)
        self.clearButton.clicked.connect(self.clear_items)

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.populate_differ_ids()

    def db_detach(self):
        self.clear_items()
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def populate_differ_ids(self):
        for row in self.Data.get_differ_ids(self.cursor):
            # TODO: add constants?
            self.leftTree.addTopLevelItem(QTreeWidgetItem([str(row[0]), str(row[1])]))
            self.rightTree.addTopLevelItem(QTreeWidgetItem([str(row[0]), str(row[1])]))

    def differ_add_response_id(self, Id):

        row = self.Data.read_responses_by_id(self.cursor, Id)
        if not row:
            return

        responseItems = [m or '' for m in list(row)]

        self.leftTree.addTopLevelItem(QTreeWidgetItem([str(row[ResponsesTable.ID]), str(row[ResponsesTable.URL])]))
        self.rightTree.addTopLevelItem(QTreeWidgetItem([str(row[ResponsesTable.ID]), str(row[ResponsesTable.URL])]))

    def clear_items(self):
        self.leftTree.clear()
        self.rightTree.clear()
        self.Data.clear_differ_items(self.cursor)

    def diff_items(self):
        """ Diff the selected items in the two panes """
        
        differ = difflib.HtmlDiff(wrapcolumn=50)
        
        # Passes if only one item is selected, otherwise it would error
        leftItem = self.leftTree.currentItem()
        rightItem = self.rightTree.currentItem()
        if leftItem is not None and rightItem is not None:
            try:
                self.Progress.show()

                leftIndex = str(leftItem.text(0))
                rightIndex = str(rightItem.text(0))
                if leftIndex != rightIndex:
                    # TODO: take content types into account
                    # TODO: can a initial match be done to detect when comparing extremely disimilar types
                    #       compute character distribution, check standard deviation
                    # TODO: this should be run in a background thread to avoid starving main loop
                    dbResponse = self.Data.read_responses_by_id(self.cursor, leftIndex)
                    leftHtml = str(dbResponse[ResponsesTable.RES_DATA])
                    dbResponse = self.Data.read_responses_by_id(self.cursor, rightIndex)
                    rightHtml = str(dbResponse[ResponsesTable.RES_DATA])
                    diffHtml = differ.make_file(leftHtml.splitlines(), rightHtml.splitlines())
                    self.diffView.setHtml(diffHtml)
                else:
                    self.diffView.setHtml('')
            except Exception, e:
                self.display_message('Failed when comparing:\n%s' % (e))
                self.diffView.setHtml('')
            finally:
                self.Progress.close()
        
    def custom_diff(self):
        """ Custom diff dialog that allows you to copy and paste content in to do
        custom diffing """
        
        #ToDo: Fix: Currently runs on exec and can't go back to the main dialog until closed
        customDiffDialog = DiffCustomDialog()
        customDiffDialog.show()
        customDiffDialog.exec_()

    def display_message(self, message):
        dialog = SimpleDialog(message)
        dialog.exec_()
        
