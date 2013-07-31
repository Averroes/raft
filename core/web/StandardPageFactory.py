#
# Factory to create new SequenceBuilderWebPages
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

from PyQt4.QtCore import QObject, SIGNAL

from .StandardWebPage import StandardWebPage

class StandardPageFactory(QObject):
    def __init__(self, framework, networkAccessManager = None, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework
        if networkAccessManager is not None:
            self.networkAccessManager = networkAccessManager
        else:
            self.networkAccessManager = framework.getNetworkAccessManager()

    def new_page(self, parent = None):
        webPage = StandardWebPage(self.framework, parent)
        webPage.setNetworkAccessManager(self.networkAccessManager)
        return webPage
