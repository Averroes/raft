#
# Search dialog
#
# Authors: 
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

from PyQt4.QtCore import (Qt, SIGNAL, QObject, pyqtSignature, QUrl, QSettings, QDir, QThread, QMutex)
from PyQt4.QtGui import *

from ui import SearchDialog

from actions import interface

from dialogs.ProgressDialog import ProgressDialog
from dialogs.RequestResponseDetailDialog import RequestResponseDetailDialog

from widgets.RequestResponseWidget import RequestResponseWidget
from widgets.ResponsesContextMenuWidget import ResponsesContextMenuWidget
from core.workers.SearchThread import SearchThread
from core.data.SearchCriteria import SearchCriteria
from core.data import ResponsesDataModel

class SearchDialog(QDialog, SearchDialog.Ui_SearchDialog):
    """ The search dialog """
    
    def __init__(self, framework, parent=None):
        super(SearchDialog, self).__init__(parent)
        self.setupUi(self)

        self.framework = framework

        # progress dialog
        self.Progress = ProgressDialog(self)

        self.searchRequestResponse = RequestResponseWidget(self.framework, self.searchTabWidget, self.searchSearchControlPlaceholder, self)

        self.searchResultsModel = ResponsesDataModel.ResponsesDataModel(self.framework, self)
        self.searchResultsTree.setModel(self.searchResultsModel)
        self.searchResultsTree.clicked.connect(self.fill_bottom)
        self.searchResultsTree.doubleClicked.connect(self.response_item_double_clicked)

        self.thread = SearchThread(self.framework, self.searchResultsModel)
        self.thread.start(QThread.LowestPriority)
        self.finished.connect(self.finishedHandler)
        self.searchPushButton.pressed.connect(self.startSearch)
        self.connect(self, SIGNAL('searchFinished()'), self.searchFinishedHandler, Qt.QueuedConnection)
        # Create context menu
        self.resultsContextMenu = ResponsesContextMenuWidget(self.framework, self.searchResultsModel, self.searchResultsTree, self)
        self.resultsContextMenu.set_currentChanged_callback(self.fill_bottom)

    def response_item_double_clicked(self, index):
        Id = interface.index_to_id(self.searchResultsModel, index)
        if Id:
            dialog = RequestResponseDetailDialog(self.framework, str(Id), self)
            dialog.show()
            dialog.exec_()

    def fill_bottom(self, index):
        if self.searchFilling:
            return
        Id = interface.index_to_id(self.searchResultsModel, index)
        if Id:
            self.searchRequestResponse.fill(str(Id))
            self.searchRequestResponse.set_search_info(str(self.searchText.text()).strip(), self.cbRegularExpression.isChecked())

    def startSearch(self):
        text = str(self.searchText.text()).strip()
        if 0 == len(text):
            return
        options = {
            'CaseSensitive' : self.cbCaseSensitive.isChecked(),
            'RegularExpression' : self.cbRegularExpression.isChecked(),
            'InvertSearch' : self.cbInvertSearch.isChecked(),
            'Wildcard' : self.cbWildcard.isChecked(),
            }
        locations = {
            'RequestHeaders' : self.cbRequestHeaders.isChecked(),
            'RequestBody' : self.cbRequestBody.isChecked(),
            'ResponseHeaders' : self.cbResponseHeaders.isChecked(),
            'ResponseBody' : self.cbResponseBody.isChecked(),
            'RequestUrl' : self.cbRequestUrl.isChecked(),
            'AnalystNotes' : self.cbAnalystNotes.isChecked(),
            }
        searchCriteria = SearchCriteria(text, options, locations)
        self.Progress.show()
        self.searchFilling = True
        self.searchRequestResponse.clear()
        self.searchResultsTree.clearSelection()
        self.searchResultsModel.clearModel()
        self.thread.startSearch(searchCriteria, self)

    def searchFinishedHandler(self):
        self.Progress.close()
        self.searchFilling = False

    def finishedHandler(self, code):
        self.thread.emit(SIGNAL('quit()'))
