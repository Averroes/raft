#
# RAFT embedded web browser 
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

from ui import RaftBrowser
from widgets.EmbeddedWebkitWidget import EmbeddedWebkitWidget
from core.web.StandardPageFactory import StandardPageFactory
from core.network.StandardNetworkAccessManager import StandardNetworkAccessManager

class RaftBrowserDialog(QDialog, RaftBrowser.Ui_RaftBrowserDialog):
    def __init__(self, framework, parent = None, options = None):
        super(RaftBrowserDialog, self).__init__(parent)
        self.setupUi(self)

        self.framework = framework
        self.networkAccessManager = StandardNetworkAccessManager(self.framework, self.framework.get_global_cookie_jar())
        self.standardPageFactory = StandardPageFactory(self.framework, self.networkAccessManager, self)
        self.embedded = EmbeddedWebkitWidget(self.framework, self.networkAccessManager, self.standardPageFactory, self.raftBrowserWebFrame, self)

        if options:
           if 'body' in options and 'url' in options:
               mimetype = options.get('mimetype') or ''
               self.embedded.open_with_content(options['url'], options['body'], mimetype)
           elif 'url' in options:
               self.embedded.open_with_url(options['url'])

        

        
