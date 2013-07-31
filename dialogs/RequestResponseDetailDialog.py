#
# Request and response detail dialog
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

from ui import RequestResponseDetailDialog
from widgets.RequestResponseWidget import RequestResponseWidget
from widgets.RequestResponseDetailWidget import RequestResponseDetailWidget

class RequestResponseDetailDialog(QDialog, RequestResponseDetailDialog.Ui_RequestResponseDetailDialog):
    def __init__(self, framework, responseId, parent = None):
        super(RequestResponseDetailDialog, self).__init__(parent)
        self.setupUi(self)
        self.framework = framework
        self.responseId = responseId

        dialogTitle = "Response Detail - #%s" % (responseId)
        self.setWindowTitle(QApplication.translate("RequestResponseDetailDialog", dialogTitle, None, QApplication.UnicodeUTF8))

        self.requestResponseWidgetDetail = RequestResponseDetailWidget(self.framework, self.detailWidget, responseId, self)
        # TODO: consider if search and update widget is needed
        self.requestResponseWidget = RequestResponseWidget(self.framework, self.tabWidget, None, self)
        self.requestResponseWidget.fill(responseId)

