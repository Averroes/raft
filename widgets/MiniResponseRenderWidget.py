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
    def __init__(self, framework, tabWidget, showRequest, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework
        QObject.connect(self, SIGNAL('destroyed(QObject*)'), self._destroyed)
        self.tabWidget = tabWidget
        self.showRequest = showRequest

        if self.showRequest:
            self.reqReqEdit_Tab = QWidget(self.tabWidget)
            self.tabWidget.addTab(self.reqReqEdit_Tab, 'Request')
            # TODO: must this hard-coded ?
            self.render_tab_index = 2
        else:
            self.render_tab_index = 1

        self.reqResEdit_Tab = QWidget(self.tabWidget)
        self.tabWidget.addTab(self.reqResEdit_Tab, 'Response')

        self.reqRenderView_Tab = QWidget(self.tabWidget)
        self.tabWidget.addTab(self.reqRenderView_Tab, 'Render')

        # TODO: a common utility method should be used to all scintilla stuff
        if self.showRequest:
            self.reqReqEdit_Layout = QVBoxLayout(self.reqReqEdit_Tab)
            self.reqReqEdit = Qsci.QsciScintilla(self.reqReqEdit_Tab)
            self.reqReqEdit.zoomTo(self.framework.get_zoom_size())
            self.reqReqEdit.setMarginLineNumbers(1, True)
            self.reqReqEdit.setMarginWidth(1, '1000')
            self.reqReqEdit.setWrapMode(1)
            self.reqReqEdit.setWrapVisualFlags(2, 1, 0)
            self.reqReqEdit_Layout.addWidget(self.reqReqEdit)

        self.reqResEdit_Layout = QVBoxLayout(self.reqResEdit_Tab)
        self.reqResEdit = Qsci.QsciScintilla(self.reqResEdit_Tab)
        self.reqResEdit.zoomTo(self.framework.get_zoom_size())
        self.reqResEdit.setMarginLineNumbers(1, True)
        self.reqResEdit.setMarginWidth(1, '1000')
        self.reqResEdit.setWrapMode(1)
        self.reqResEdit.setWrapVisualFlags(2, 1, 0)
        self.reqResEdit_Layout.addWidget(self.reqResEdit)

        self.reqRenderView_Layout = QVBoxLayout(self.reqRenderView_Tab)
        self.requesterPageFactory = StandardPageFactory(self.framework, None, self)
        self.reqRenderView = RenderingWebView(self.framework, self.requesterPageFactory, self.tabWidget)
        self.reqRenderView_Layout.addWidget(self.reqRenderView)

        self.request_url = None

        self.tabWidget.currentChanged.connect(self.do_render_apply)

        self.framework.subscribe_zoom_in(self.zoom_in_scintilla)
        self.framework.subscribe_zoom_out(self.zoom_out_scintilla)

    def _destroyed(self):
        self.framework.unsubscribe_zoom_in(self.zoom_in_scintilla)
        self.framework.unsubscribe_zoom_out(self.zoom_out_scintilla)

    def fill_from_response(self, url, headers, body, content_type = ''):
        self.reqRenderView.fill_from_response(url, headers, body, content_type)

    def populate_response_content(self, url, req_headers, req_body, res_headers, res_body, res_content_type = ''):
            
        self.request_url = url
        self.request_headers = req_headers
        self.request_body = req_body
        self.response_headers = res_headers
        self.response_body = res_body
        self.response_content_type = res_content_type

        if self.showRequest:
            self.reqReqEdit.setText(ContentHelper.getCombinedText(self.request_headers, self.request_body, ''))

        # TODO: should support different lexers based on content type
        lexerInstance = Qsci.QsciLexerHTML(self.reqResEdit)
        lexerInstance.setFont(self.framework.get_font())
        self.reqResEdit.setLexer(lexerInstance)
        # TODO: should verify trailing newlines?
        self.reqResEdit.setText(ContentHelper.getCombinedText(self.response_headers, self.response_body, self.response_content_type))

        self.do_render_apply(self.tabWidget.currentIndex())

    def do_render_apply(self, index):
        if self.render_tab_index == index:
            if self.request_url:
                self.fill_from_response(self.request_url, self.response_headers, self.response_body, self.response_content_type)

    def clear_response_render(self):
        if self.showRequest:
            self.reqReqEdit.setText('')
        self.reqResEdit.setText('')
        self.reqRenderView.setHtml('', QUrl('about:blank'))
        self.request_url = ''
        self.request_headers = b''
        self.request_body = b''
        self.response_headers = b''
        self.response_body = b''
        self.response_content_type = ''
        

    def zoom_in_scintilla(self):
        if self.showRequest:
            self.reqReqEdit.zoomIn()
        self.reqResEdit.zoomIn()

    def zoom_out_scintilla(self):
        if self.showRequest:
            self.reqReqEdit.zoomOut()
        self.reqResEdit.zoomOut()
