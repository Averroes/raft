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
            lines = headers.splitlines()
            pos = 0
            for line in lines:
                if ':' in line:
                    name, value = [x.strip() for x in line.split(':', 1)]
                    if 'content-type' == name.lower():
                        content_type = value
                        break
        if content_type:
            pos = content_type.find(';')
            if pos != -1:
                content_type = content_type[0:pos].strip()
                pos = content_type.find('charset=', pos)
                if pos != -1:
                    charset = content_type[pos+8:].strip()
        else:
            content_type = 'text/html'
            charset = 'utf-8'

        qurl = QUrl.fromEncoded(url)

        # TODO: improve setting for non-html content, especially css

        if 'html' in content_type:
            self.setHtml(body, qurl)
        else:
            self.setContent(body, content_type, qurl)



