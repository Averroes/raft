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

from PyQt4.QtCore import (Qt, QObject, SIGNAL, QUrl, QByteArray, QIODevice, QBuffer)
from PyQt4.QtNetwork import *

from core.network.NetworkResponse import NetworkResponse
from core.network.NetworkRequest import NetworkRequest

class NetworkRequester(QObject):
    def __init__(self, framework, networkAccessManager, callback, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework
        self.networkAccessManager = networkAccessManager
        self.callback = callback

    def GET(self, url, headers = {}):
        self.send('GET', url, headers, None)

    def POST(self, url, body, headers = {}, enctype = 'application/x-www-form-urlencoded'):
        content_encoding = None
        for name, value in headers.iteritems():
            if 'content-encoding' == name.lower():
                content_encoding = value
        if not content_encoding:
            headers['Content-Encoding'] = enctype

        self.send('POST', url, headers, body)

    def send(self, method, url, headers, body, context = None):
        qurl = QUrl.fromEncoded(url)
        request = QNetworkRequest()
        request.setUrl(qurl)
        method = self.translate_method(method, request)

        host, useragent, content_encoding = None, None, None
        for name, value in headers.iteritems():
            lname = name.lower()
            if 'user-agent' == lname:
                useragent = value
            elif 'host' == lname:
                host = value
            elif 'content-encoding' == lname:
                content_encoding = value
            elif 'content-length' == lname: 
                continue
            request.setRawHeader(name, value)

        if not host:
            request.setRawHeader('Host', str(qurl.host()))
        if not useragent:
            request.setRawHeader('User-Agent', self.framework.useragent())
        if 'POST' == method and not content_encoding:
            request.setRawHeader('Content-Encoding', 'application/x-www-form-urlencoded')

        if not body:
            device = None
            if method in ('POST', 'PUT', 'CUSTOM'): # TODO: determine specific methods that expect content?
                request.setRawHeader('Content-Length', '0')
        elif method in ('GET', 'HEAD', 'DELETE'):
            # can't have body, because not supported by Qt network logic
            device = None
        else:
            request.setRawHeader('Content-Length', str(len(body)))
            data = QByteArray(body)
            device = QBuffer(self)
            device.setData(data)
            device.open(QIODevice.ReadOnly)

        request.setAttribute(request.CacheLoadControlAttribute, request.AlwaysNetwork)

        if 'GET' == method:
            reply = self.networkAccessManager.get(request)
        elif 'HEAD' == method:
            reply = self.networkAccessManager.head(request)
        elif 'DELETE' == method:
            reply = self.networkAccessManager.head(request)
        elif 'POST' == method:
            reply = self.networkAccessManager.post(request, device)
        elif 'PUT' == method:
            reply = self.networkAccessManager.put(request, device)
        else:
            reply = self.networkAccessManager.sendCustomRequest(request, method, device)

        response = NetworkResponse(self.framework, self.callback, reply, context, self)
        return NetworkRequest(request, reply, response, context, self)

    def translate_method(self, method, request):
        method = method.upper()
        if method not in ('HEAD', 'GET', 'POST', 'PUT', 'DELETE'):
            request.setAttribute(request.CustomVerbAttribute, method)
        return method

