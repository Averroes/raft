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
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt4.QtCore import QTimer, SIGNAL, QUrl, QObject, QByteArray

from io import StringIO, BytesIO
import time, re, traceback
from urllib import parse as urlparse

class StoreNetworkReply(QNetworkReply):
    def __init__(self, framework, url, operation, request, requestContent, cookieJar, reply, parent = None):
        QNetworkReply.__init__(self, parent)
        self.framework = framework
        self.Data = self.framework.getDB()
        self.__url = url
        self.__request = request
        self.__reply = reply

        self.reqUrl = request.url()
        self.requestContent = requestContent
        self.requestTime = time.time()
        self.data_io = BytesIO()
        self.response_data = b''
        self.datalen = 0
        self.offset = 0
        self.response_status = ''
        self.responseHeaders = b''
        self.is_finished = False
        self.requestId = ''
        self.xrefId = ''
        self.pendingData = b''

        self.__populate_request_info(operation, cookieJar)

        QObject.connect(self.__reply, SIGNAL('sslErrors(const QList<QSslError> &)'), self.handle_sslErrors)
        QObject.connect(self.__reply, SIGNAL('error(QNetworkReply::NetworkError)'), self.handle_errors)
        QObject.connect(self.__reply, SIGNAL('uploadProgress(qint64, qint64)'), self.handle_uploadProgress)
        QObject.connect(self.__reply, SIGNAL('downloadProgress(qint64, qint64)'), self.handle_downloadProgress)
        QObject.connect(self.__reply, SIGNAL('readyRead()'), self.handle_readyRead)
        QObject.connect(self.__reply, SIGNAL('metaDataChanged()'), self.handle_metaDataChanged)
        QObject.connect(self.__reply, SIGNAL('finished()'), self.handle_finished)

        self.debug_print('__init__')
        self.setOperation(self.__reply.operation())
        self.setReadBufferSize(self.__reply.readBufferSize())
        self.setRequest(self.__reply.request())
        self.setUrl(self.__reply.url())

        self.open(self.ReadOnly | self.Unbuffered)

    def __populate_request_info(self, operation, cookieJar):

        self.method = self.__translate_operation(operation)

        varId = self.__request.attribute(QNetworkRequest.User + 1)
        if varId is not None:
            self.requestId = varId

        varId = self.__request.attribute(QNetworkRequest.User + 2)
        if varId is not None:
            self.xrefId = varId

        parsed = urlparse.urlsplit(self.__url)
        relative_url = parsed.path
        if parsed.query:
            relative_url += '?' + parsed.query
        if parsed.fragment:
            # TODO: will this ever happen?
            relative_url += '#' + parsed.fragment

        headers_io = BytesIO()
        headers_io.write(self.method.encode('ascii'))
        headers_io.write(b' ')
        headers_io.write(relative_url.encode('utf-8'))
        headers_io.write(b' HTTP/1.1\r\n')
        host = ''
        for bname in self.__request.rawHeaderList():
            bvalue = self.__request.rawHeader(bname)
            name = bname.data()
            value = bvalue.data()
            headers_io.write(name)
            headers_io.write(b': ')
            headers_io.write(value)
            headers_io.write(b'\r\n')
            if b'host' == name.lower():
                host = value.decode('utf-8')

        if cookieJar:
            cookiesList = cookieJar.cookiesForUrl(self.__request.url())
            if len(cookiesList) > 0:
                headers_io.write(b'Cookie: ')
                first = True
                for cookie in cookiesList:
                    if not first:
                        headers_io.write(b'; ')
                    else:
                        first = False
                    headers_io.write(cookie.name())
                    headers_io.write(b'=')
                    headers_io.write(cookie.value())

        headers_io.write(b'\r\n')

        if not host:
            host = parsed.hostname

        self.host = host
        self.requestHeaders = headers_io.getvalue()

    def __translate_operation(self, operation):
        if QNetworkAccessManager.HeadOperation == operation:
            return 'HEAD'
        elif QNetworkAccessManager.GetOperation == operation:
            return 'GET'
        elif QNetworkAccessManager.PutOperation == operation:
            return 'PUT'
        elif QNetworkAccessManager.PostOperation == operation:
            return 'POST'
        elif QNetworkAccessManager.DeleteOperation == operation:
            return 'DELETE'
        else:
            # CUSTOM
            return self.__request.attribute(self.__request.CustomVerbAttribute).data().decode('ascii','ignore')

    def __attr__(self, name):
        self.debug_print('__attr__', name)
        r = attr(self.__reply, name)
        return r

    def debug_print(self, *args):
#        print((args, self.__url))
        pass

    def manager(self):
        return self.__reply.manager()

    def isFinished(self):
        return self.is_finished

    def isRunning(self):
        return not self.is_finished

    def handle_errors(self, code):
        self.debug_print('error: %d' % (code))
        self.emit(SIGNAL('error(QNetworkReply::NetworkError)'), code)

    def handle_sslErrors(self, list):
        # TODO: should check
        self.debug_print('ignoring ssl errors', list)
        self.__reply.ignoreSslErrors()
        self.setSslConfiguration(self.__reply.sslConfiguration())
        self.emit(SIGNAL('sslErrors(const QList<QSslError> &)'), list)

    def handle_readyRead(self):
        self.debug_print('handling read ready', self.__reply.bytesAvailable())
        self.emit(SIGNAL('readyRead()'))

    def handle_metaDataChanged(self):
        self.debug_print('handling meta data changed')

        # initialize our state based on child reply
        reply = self.__reply

        redirectTarget = reply.attribute(QNetworkRequest.RedirectionTargetAttribute)
        if redirectTarget is not None and type(redirectTarget) == QUrl:
            self.debug_print('redirectTarget received', redirectTarget.toEncoded().data().decode('utf-8'))
            # TODO: validate we want to do this
            self.setAttribute(QNetworkRequest.RedirectionTargetAttribute, redirectTarget)

        attributes = (QNetworkRequest.HttpStatusCodeAttribute, 
                      QNetworkRequest.HttpReasonPhraseAttribute, 
                      QNetworkRequest.ConnectionEncryptedAttribute, 
                      QNetworkRequest.HttpPipeliningWasUsedAttribute,
                      QNetworkRequest.SourceIsFromCacheAttribute)
        for attribute in attributes:
            val = reply.attribute(attribute)
            if val is not None:
                self.setAttribute(attribute, val)

        self.setError(reply.error(), reply.errorString())

        val = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if val is not None:
            status = val
            self.response_status = val
            message = reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute)
            headers_io = BytesIO()
            headers_io.write(b'HTTP/1.1 ')
            headers_io.write(str(self.response_status).encode('ascii'))
            headers_io.write(b' ')
            headers_io.write(message.encode('utf-8')) # TODO: is server HTTP version exposed?
            headers_io.write(b'\r\n')
            for bname in reply.rawHeaderList():
                bvalue = reply.rawHeader(bname)
                headers_io.write(bname.data())
                headers_io.write(b': ')
                headers_io.write(bvalue.data())
                headers_io.write(b'\r\n')
                self.setRawHeader(bname, bvalue)
            headers_io.write(b'\r\n')
            self.responseHeaders = headers_io.getvalue()
        else:
            for bname in reply.rawHeaderList():
                bvalue = reply.rawHeader(bname)
                self.setRawHeader(bname, bvalue)

        self.emit(SIGNAL('metaDataChanged()'))

    def handle_uploadProgress(self, bytesSent, bytesTotal):
        self.debug_print('handling uploadProgress', bytesSent, bytesTotal)
        self.emit(SIGNAL('uploadProgress(qint64, qint64)'), bytesSent, bytesTotal)

    def handle_downloadProgress(self, bytesReceived, bytesTotal):
        self.debug_print('handling downloadProgress', bytesReceived, bytesTotal)
        self.emit(SIGNAL('downloadProgress(qint64, qint64)'), bytesReceived, bytesTotal)

    def calculate_redirect(self, redirectTarget):
        pass

    def handle_finished(self):
        self.debug_print('handling finished', self.__url)

        finishTime = time.time()
        elapsed = int((finishTime - self.requestTime)*1000) # TODO: verify

        available = self.__reply.bytesAvailable()
        while available > 0:
            data = self.__reply.read(available)
            if not data:
                break
            self.pendingData += data
            self.data_io.write(data)
            available = self.__reply.bytesAvailable()

        data_bytes = self.data_io.getvalue()
        if 0 == len(data_bytes):
            dbytes = self.__reply.readAll()
            if dbytes is not None:
                data_bytes = dbytes.data()

        self.response_data = data_bytes
        self.datalen = len(data_bytes)
        self.offset = 0

        fromCache = bool(self.__reply.attribute(QNetworkRequest.SourceIsFromCacheAttribute))
        if not self.response_status or fromCache or self.__url.startswith('about:') or self.__url.startswith('data:'):
            pass
        else:
            # no status means no response that can be stored
            status = self.response_status

            requestContent = b''
            if self.requestContent is not None:
                if hasattr(self.requestContent, 'get_intercepted_data'):
                    requestContent = self.requestContent.get_intercepted_data()
                elif hasattr(self.requestContent, 'data'):
                    requestContent = self.requestContent.data().data()

            contentType = self.__reply.header(QNetworkRequest.ContentTypeHeader)
            if not contentType:
                # TODO: implement real "sniff" content-type
                if -1 != self.response_data.find(b'<html'):
                    contentType = 'text/html'
                    self.setRawHeader('Content-Type', contentType.encode('utf-8'))
                    # reply.setHeader(QNetworkRequest.ContentTypeHeader, contentType)

            # TODO: determine hostip
            hostip = None
            insertlist = [None, self.__url, self.requestHeaders, requestContent, self.responseHeaders, self.response_data,
                          status, self.datalen, elapsed, time.asctime(time.localtime(self.requestTime)), None, None, None, 
                          self.method, hostip, contentType, '%s-%s' % ('RAFT', 'ResponseReader'), self.host]

            # use a fresh cursor to avoid threading issues
            cursor = self.Data.allocate_thread_cursor()
            rowid = self.Data.insert_responses(cursor, insertlist)
            cursor.close()
            self.Data.release_thread_cursor(cursor)

            # TODO: should use a separate constant?
            self.setAttribute(QNetworkRequest.User, rowid)
            self.setAttribute(QNetworkRequest.User + 1, self.requestId)
            self.setAttribute(QNetworkRequest.User + 2, self.xrefId)

            self.framework.signal_response_data_added()
        
        self.is_finished = True
        self.emit(SIGNAL("readyRead()"))
        self.emit(SIGNAL("finished()"))
#        QTimer.singleShot(0, self, SIGNAL("finished()"))

    def abort(self):
        try:
            self.debug_print('abort')
            self.__reply.abort()
        except AttributeError as e:
            # TODO: determine where corruption is occuring
            self.debug_print('abort error', e)
        self.is_finished = True

    def isSequential(self):
        return True

    def bytesAvailable(self):
        try:
            if self.is_finished and self.pendingData:
                available = len(self.pendingData)
            else:
                available = self.__reply.bytesAvailable()
            self.debug_print('bytes available', available)
            return available
        except AttributeError as e:
            # TODO: determine where corruption is occuring
            self.debug_print('bytesAvailable failed', e)
            return 0

    def canReadLine(self):
        self.debug_print('canReadLine', self.__reply.canReadLine())
        return self.__reply.canReadLine()

    def readData(self, maxSize):
        self.debug_print('readData', maxSize, self.is_finished, self.pendingData)
        if self.is_finished and self.pendingData:
            if len(self.pendingData) > maxSize:
                data = self.pendingData[0:maxSize]
                self.pendingData = self.pendingData[maxSize:]
            else:
                data = self.pendingData
                self.pendingData = b''
        else:
            data = self.__reply.read(maxSize)
            if data:
                self.data_io.write(data)

        self.debug_print('returning data', len(data), data)
        return data
    
    def readAll(self):
        self.debug_print('readAll', self.response_data)
        return QByteArray(self.response_data)
