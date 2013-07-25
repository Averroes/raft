#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#         Nathan Hamiel
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

from PyQt4.QtCore import Qt, QObject, SIGNAL, QUrl
from PyQt4.QtGui import *
from PyQt4 import Qsci

from core.web.StandardPageFactory import StandardPageFactory
from core.web.RenderingWebView import RenderingWebView
from utility import ContentHelper

class MiniResponseRenderWidget(QObject):
    def __init__(self, framework, tabWidget, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework
        self.tabWidget = tabWidget

        self.reqResEdit_Tab = QWidget(self.tabWidget)
        self.tabWidget.addTab(self.reqResEdit_Tab, 'Response')

        self.reqRenderView_Tab = QWidget(self.tabWidget)
        self.tabWidget.addTab(self.reqRenderView_Tab, 'Render')

        # TODO: a common utility method should be used to all scintilla stuff
        self.reqResEdit_Layout = QVBoxLayout(self.reqResEdit_Tab)
        self.reqRespEdit = Qsci.QsciScintilla(self.reqResEdit_Tab)
        self.reqRespEdit.zoomTo(self.framework.get_zoom_size())
        self.framework.subscribe_zoom_in(lambda: self.reqRespEdit.zoomIn())
        self.framework.subscribe_zoom_out(lambda: self.reqRespEdit.zoomOut())
        self.reqRespEdit.setMarginLineNumbers(1, True)
        self.reqRespEdit.setMarginWidth(1, '1000')
        self.reqRespEdit.setWrapMode(1)
        self.reqRespEdit.setWrapVisualFlags(2, 1, 0)
        self.reqResEdit_Layout.addWidget(self.reqRespEdit)

        self.reqRenderView_Layout = QVBoxLayout(self.reqRenderView_Tab)
        self.requesterPageFactory = StandardPageFactory(self.framework, None, self)
        self.reqRenderView = RenderingWebView(self.framework, self.requesterPageFactory, self.tabWidget)
        self.reqRenderView_Layout.addWidget(self.reqRenderView)

        self.request_url = None

        self.tabWidget.currentChanged.connect(self.do_render_apply)

    def fill_from_response(self, url, headers, body, content_type = ''):
        self.reqRenderView.fill_from_response(url, headers, body, content_type)

    def populate_response_content(self, url, headers, body, content_type = ''):
            
        self.request_url = url
        self.response_headers = headers
        self.response_body = body
        self.response_content_type = content_type

        # TODO: should support different lexers based on content type
        lexerInstance = Qsci.QsciLexerHTML(self.reqRespEdit)
        lexerInstance.setFont(self.framework.get_font())
        self.reqRespEdit.setLexer(lexerInstance)
        # TODO: should verify trailing newlines?
        self.reqRespEdit.setText(ContentHelper.getCombinedText(self.response_headers, self.response_body, self.response_content_type))

        self.do_render_apply(self.tabWidget.currentIndex())

    def do_render_apply(self, index):
        # TODO: must this hard-coded ?
        if 1 == index:
            if self.request_url:
                self.fill_from_response(self.request_url, self.response_headers, self.response_body, self.response_content_type)

    def clear_response_render(self):
        self.reqRespEdit.setText('')
        self.reqRenderView.setHtml('', QUrl('about:blank'))
        self.request_url = ''
        self.response_headers = b''
        self.response_body = b''
        self.response_content_type = ''
        
