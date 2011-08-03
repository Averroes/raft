#
# Implements webview for DOM fuzzing
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

import PyQt4

from PyQt4 import QtWebKit, QtNetwork
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from core.web.DomFuzzerWebPage import DomFuzzerWebPage
from core.network.OfflineNetworkAccessManager import OfflineNetworkAccessManager

class DomFuzzerWebView(QtWebKit.QWebView):
    def __init__(self, framework, callbackLogger, parent = None):
        QtWebKit.QWebView.__init__(self, parent)
        self.framework = framework
        self.__networkAccessManager = OfflineNetworkAccessManager(self.framework, None)
        self.__page = DomFuzzerWebPage(self.framework, callbackLogger, self) # TODO: or parent?
        self.__page.setNetworkAccessManager(self.__networkAccessManager)
        self.setPage(self.__page)

