
#
# Confirm Dialog
#
# Authors: 
#          Nathan Hamiel
#
# Copyright (c) 2013 RAFT Team
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

from PyQt4.QtCore import (Qt, SIGNAL, QObject)
from PyQt4.QtGui import *

def display_confirm_dialog(self, message):
        response = QMessageBox.question(self, 'Confirm', message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if 0 != (response & QMessageBox.Yes):
            return True
        else:
            return False