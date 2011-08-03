#
# Wrap another network cache and log debug messages
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

class NetworkCacheLogger(QtNetwork.QAbstractNetworkCache):
    def __init__(self, framework, cache, parent = None):
        QtNetwork.QAbstractNetworkCache.__init__(self, parent)
        self.nc = cache

    def __attr__(self, name):
        print('NetworkCache: [%s]' % (name))
        return getattr(self.nc, msg)

    def insert(self, device):
        msg = 'NetworkCache: [%s](%s)' % ('insert', device)
        r = self.nc.insert(device)
        print('%s -> %s' % (msg, r))
        return r

    def metaData(self, url):
        msg = 'NetworkCache: [%s](%s)' % ('metaData', url)
        r = self.nc.metaData(url)
        print('%s -> %s, isValid=%s' % (msg, r, r.isValid()))
        print('\n'.join(['%s: %s' % (n, v) for n,v in r.rawHeaders()]))
        return r

    def data(self, url):
        msg = 'NetworkCache: [%s](%s)' % ('data', url)
        r = self.nc.data(url)
        if r:
            print('%s -> %s, isOpen=%s' % (msg, r, r.isOpen()))
        return r

    def prepare(self, metaData):
        msg = 'NetworkCache: [%s](%s)' % ('prepare', metaData)
        r = self.nc.prepare(metaData)
        print('%s -> %s' % (msg, r))
#        print('\n'.join(['%s: %s' % (n, v) for n,v in metaData.rawHeaders()]))
        return r

    def remove(self, url):
        msg = 'NetworkCache: [%s](%s)' % ('remove', url)
        r = self.nc.remove(url)
        print('%s -> %s' % (msg, r))
        return r

    def updateMetaData(self, metaData):
        msg = 'NetworkCache: [%s](%s)' % ('updateMetaData', metaData)
        r = self.nc.updateMetaData(metaData)
        print('%s -> %s' % (msg, r))
        print('\n'.join(['%s: %s' % (n, v) for n,v in metaData.rawHeaders()]))
