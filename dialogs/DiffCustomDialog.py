#
# custom diff dialog to show differences in arbitrary content
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

from ui import DiffCustomDialog

class DiffCustomDialog(QDialog, DiffCustomDialog.Ui_CustomDiffDialog):
    """ Display custom diff dialog """
    
    def __init__(self, parent=None):
        super(DiffCustomDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.diffButton.clicked.connect(self.diff)
        self.closeButton.clicked.connect(self.close_clicked)
        
    def diff(self):
        """ Diff the items in the two panes """
        
        differ = difflib.HtmlDiff(wrapcolumn=50)
        
        leftValue = str(self.leftEdit.toPlainText())
        rightValue = str(self.rightEdit.toPlainText())
        
        diffHtml = differ.make_file(leftValue.splitlines(), rightValue.splitlines())
        self.diffView.setHtml(diffHtml)

    def close_clicked(self):
        self.close()
        
