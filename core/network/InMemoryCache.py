#
# Implementation of in-memory cache
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

class InMemoryCache(QtNetwork.QAbstractNetworkCache):
    def __init__(self, framework, parent = None):
        QtNetwork.QAbstractNetworkCache.__init__(self, parent)
        self.framework = framework
        self.framework.subscribe_responses_cleared(self.responses_cleared)
        self.size = 0
        self.cache = {} # list of [metaData, device, ctime] entries by url
        self.outstanding = {}
    
    def responses_cleared(self):
        self.clear()
        
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
        # TODO: implement max size of cache using LRU approach
        for k in self.outstanding.keys():
            if self.outstanding[k] == device:
                self.size += device.size()
                self.cache[k][1] = device.data()
                device = None
                return
        else:
            raise Exception('Failed to find outstanding entry on cache insert')

    def metaData(self, url):
        k = url.toEncoded()
        if self.cache.has_key(k):
            metaData, buf, mtime = self.cache[k]
            if buf:
                return metaData
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
            return True
        return False

    def updateMetaData(self, metaData):
        url = metaData.url().toEncoded()
        if self.cache.has_key(url):
            self.cache[url][0] = metaData
