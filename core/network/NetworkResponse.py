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

from PyQt4.QtCore import (Qt, QObject, SIGNAL, QUrl, QByteArray, QIODevice, QMetaType)
from PyQt4.QtNetwork import *

from io import StringIO, BytesIO

from core.database.constants import ResponsesTable

class NetworkResponse(QObject):
    def __init__(self, framework, callback, reply, context, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework
        self.reply = reply
        self.callback = callback
        self.context = context
        QObject.connect(self.reply, SIGNAL('sslErrors(const QList<QSslError> &)'), self.reply_ssl_errors)
        QObject.connect(self.reply, SIGNAL('error(QNetworkReply::NetworkError)'), self.reply_error)
        QObject.connect(self.reply, SIGNAL('finished()'), self.reply_finished)
        
    def reply_finished(self):
        response_id = 0
        status = None
        body, headers = (b'', b'')

        fetched = False
        var = self.reply.attribute(QNetworkRequest.User)
        if var is not None:
            response_id = var
            if 0 != response_id:
                Data = self.framework.getDB()
                cursor = Data.allocate_thread_cursor()
                row = Data.read_responses_by_id(cursor, response_id)
                if row:
                    response_item = [m or '' for m in row]
                    status = str(response_item[ResponsesTable.STATUS])
                    content_type = str(response_item[ResponsesTable.RES_CONTENT_TYPE])
                    headers = bytes(response_item[ResponsesTable.RES_HEADERS])
                    body = bytes(response_item[ResponsesTable.RES_DATA])
                    fetched = True
                cursor.close()
                Data.release_thread_cursor(cursor)
                Data, cursor = None, None
        if status is None:
            status = self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status:
            try:
                status = int(status)
            except ValueError as e:
                self.framework.debug_log('invalid status code value', e)
                # TODO: should log bogus code value
                pass
        if not fetched:
            # TODO: refactor this header response construction
            headers_io = BytesIO()
            message = self.reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute) or ''
            content_type = self.reply.header(QNetworkRequest.ContentTypeHeader)
            headers_io.write(b'HTTP/1.1 ')  # TODO: is server HTTP version exposed?
            headers_io.write(str(status).encode('ascii'))
            headers_io.write(b' ')
            headers_io.write(message.encode('utf-8'))
            headers_io.write(b'\r\n')
            for bname in self.reply.rawHeaderList():
                bvalue = self.reply.rawHeader(bname)
                headers_io.write(bname)
                headers_io.write(b': ')
                headers_io.write(bvalue)
                headers_io.write(b'\r\n')
            headers_io.write(b'\r\n')
            headers = headers_io.getvalue()

            data_bytes = self.reply.readAll()
            if data_bytes:
                body = data_bytes

        self.response_id = response_id
        self.status = status
        self.content_type = content_type
        self.headers = headers
        self.body = body
        self.callback(self)

    def reply_error(self, error):
        # TODO: log
        print(('ignoring', error))
        pass

    def reply_ssl_errors(self, ssl_errors):
        # TODO: record information
        # TODO: add support for client CA
        self.reply.ignoreSslErrors()
