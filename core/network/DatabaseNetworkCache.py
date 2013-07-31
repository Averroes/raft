#
# Cache implementation that reads from the RAFT database
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
from PyQt4.QtCore import *
from PyQt4 import QtNetwork
import time

from core.database.constants import ResponsesTable

class DatabaseNetworkCache(QtNetwork.QAbstractNetworkCache):
    def __init__(self, framework, parent = None):
        QtNetwork.QAbstractNetworkCache.__init__(self, parent)
        self.framework = framework
        self.size = 0
        self.cache = {} # list of [metaData, device, ctime] entries by url
        self.outstanding = {}

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.clear()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None
 
    def cacheSize(self):
        return self.size

    def clear(self):
        for k in self.cache.keys():
            metaData, buf, mtime = self.cache.pop(k)
            if buf:
                self.size -= buf.length()
                buf.clear()
            metaData, buf = None, None            

    def data(self, url):
        k = url.toEncoded()
        if self.cache.has_key(k):
            buf = self.cache[k][1]
            device = QBuffer(buf)
            device.open(QIODevice.ReadOnly|QIODevice.Unbuffered)
            return device
        return None

    def insert(self, device):
        for k in self.outstanding.keys():
            if self.outstanding[k] == device:
                self.size += device.size()
                self.cache[k][1] = device.data()
                device = None
                return
        else:
            raise Exception('Failed to find outstanding entry on cache insert')

    def metaData(self, url):
        print(self.cache.keys())
        k = url.toEncoded()
        if self.cache.has_key(k):
            metaData, buf, mtime = self.cache[k]
            if buf:
                return metaData
        responses = []
        for row in self.Data.read_responses_by_url(self.cursor, k):
            response = [m or '' for m in row]
            if int(response[ResponsesTable.RES_LENGTH]) > 0 and str(response[ResponsesTable.STATUS]).startswith('2'):
                responses.append(response)
        if len(responses) > 0:
            metaData = QtNetwork.QNetworkCacheMetaData()
            metaData.setUrl(url)
            headers = str(responses[-1][ResponsesTable.RES_HEADERS])
            rawHeaders = []
            for line in headers.splitlines():
                if ':' in line:
                    name, value = [m.strip() for m in line.split(':', 1)]
                    rawHeaders.append((QByteArray(name), QByteArray(value)))
                    try:
                        if 'last-modified' == name.lower():
                            metaData.setLastModified(QDateTime.fromString(value))
                        elif 'expires' == name.lower():
                            metaData.setExpirationDate(QDateTime.fromString(value))
                    except Exception, e:
                        print('ignoring error: %s' % e)

            metaData.setRawHeaders(rawHeaders)
            buf = QByteArray(str(responses[-1][ResponsesTable.RES_DATA]))
            self.cache[k] = [metaData, buf, time.time()]
        else:
            # return non-valid
            metaData = QtNetwork.QNetworkCacheMetaData()
        return metaData

    def prepare(self, metaData):
        k = metaData.url().toEncoded()
        self.cache[k] = [metaData, None, time.time()]
        device = QBuffer()
        device.open(QIODevice.ReadWrite|QIODevice.Unbuffered)
        self.outstanding[k] = device
        return device

    def remove(self, url):
        k = url.toEncoded()
        if self.outstanding.has_key(k):
            device = self.outstanding.pop(k)
            device = None
        if self.cache.has_key(k):
            metaData, buf, mtime = self.cache.pop(k)
            if buf:
                self.size -= buf.length()
                buf.clear()
            metaData, buf = None, None
        return False

    def updateMetaData(self, metaData):
        url = metaData.url().toEncoded()
        if self.cache.has_key(url):
            self.cache[url][0] = metaData

