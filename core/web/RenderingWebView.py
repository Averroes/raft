#
# Implements a embedded browser widget
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

from utility import ContentHelper

class RenderingWebView(QtWebKit.QWebView):
    def __init__(self, framework, pageFactory, parent = None):
        QtWebKit.QWebView.__init__(self, parent)
        self.framework = framework
        self.pageFactory = pageFactory
        self.setPage(self.pageFactory.new_page(self))
    
    def fill_from_db(self, responseId, responseUrl):
        if responseId and responseUrl:
            request = QtNetwork.QNetworkRequest(QUrl(responseUrl))
            request.setRawHeader(self.framework.X_RAFT_ID, str(responseId))
            self.load(request)
        else:
            self.setHtml('', 'about:blank')

    def fill_from_response(self, url, headers, body, content_type = None):
        if not url:
            url = 'about:blank'

        if not content_type:
            content_type = ContentHelper.getContentTypeFromHeaders(headers)

        charset = ContentHelper.getCharSet(content_type)

        qurl = QUrl.fromEncoded(url)

        # TODO: improve setting for non-html content, especially css
        self.setContent(body, content_type, qurl)



