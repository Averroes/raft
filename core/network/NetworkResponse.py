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

from cStringIO import StringIO

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
        status = ''
        body, headers = ('', '')

        fetched = False
        var = self.reply.attribute(QNetworkRequest.User)
        if var.isValid() and var.type() == QMetaType.Int:
            response_id = int(var.toInt()[0])
            if 0 != response_id:
                Data = self.framework.getDB()
                cursor = Data.allocate_thread_cursor()
                row = Data.read_responses_by_id(cursor, response_id)
                if row:
                    response_item = [m or '' for m in row]
                    status = str(response_item[ResponsesTable.STATUS])
                    content_type = str(response_item[ResponsesTable.RES_CONTENT_TYPE])
                    headers = str(response_item[ResponsesTable.RES_HEADERS])
                    body = str(response_item[ResponsesTable.RES_DATA])
                    fetched = True
                cursor.close()
                Data.release_thread_cursor(cursor)
                Data, cursor = None, None
        if not status:
            status = str(self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute).toString())
        if status:
            try:
                status = int(status)
            except ValueError, e:
                print(e)
                # TODO: should log bogus code value
                pass
        if not fetched:
            headers_io = StringIO()
            message = str(self.reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute).toString())
            content_type = str(self.reply.header(QNetworkRequest.ContentTypeHeader))
            headers_io.write('HTTP/1.1 %s %s\r\n' % (status, message)) # TODO: is server HTTP version exposed?
            for bname in self.reply.rawHeaderList():
                bvalue = self.reply.rawHeader(bname)
                name = str(bname)
                value = str(bvalue)
                headers_io.write('%s: %s\r\n' % (name, value))
            headers_io.write('\r\n')
            headers = headers_io.getvalue()

            bytes = self.reply.readAll()
            if bytes:
                body = str(bytes)

        self.response_id = response_id
        self.status = status
        self.content_type = content_type
        self.headers = headers
        self.body = body
        self.callback(self)

    def reply_error(self, error):
        # TODO: log
        print('ignoring', error)
        pass

    def reply_ssl_errors(self, ssl_errors):
        # TODO: record information
        # TODO: add support for client CA
        self.reply.ignoreSslErrors()
