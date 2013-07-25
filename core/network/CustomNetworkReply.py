# 
# this class creates a custom network reply from response data
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

from PyQt4 import QtNetwork
from PyQt4.QtCore import QTimer, SIGNAL, QUrl, QObject

# based on http://doc.qt.nokia.com/qq/32/qq32-webkit-protocols.html

class CustomNetworkReply(QtNetwork.QNetworkReply):
    def __init__(self, parent, url, rawHeaders, data):
        QtNetwork.QNetworkReply.__init__(self, parent)
        self.data =data
        self.datalen = len(self.data)
        self.offset = 0

        self.setUrl(url)
        self.open(self.ReadOnly | self.Unbuffered)
        for line in rawHeaders.splitlines():
            if b':' in line:
                name, value = line.split(b':', 1)
                self.setRawHeader(name, value)

        QTimer.singleShot(0, self, SIGNAL("metaDataChanged()"))
        QTimer.singleShot(0, self, SIGNAL("readyRead()"))
        QTimer.singleShot(0, self, SIGNAL("finished()"))

    def abort(self):
        pass

    def isSequential(self):
        return True

    def bytesAvailable(self):
        available = self.datalen - self.offset
#        print('bytesavailable: %d (%s)' % (available, self.url().toString()))
        if available < 0:
            available = 0
        return available

    def canReadLine(self):
        return data[self.offset:].index(b'\n') != -1 and QtNetwork.QNetworkReply.canReadLine(self)

    def readData(self, maxSize):
#        print('readData: %s (%s)' % (maxSize, self.url().toString()))
        if self.offset > self.datalen:
            return b'' # TODO: was None, then -1, does it matter?
        if self.offset + maxSize > self.datalen:
            maxSize = self.datalen - self.offset
        data = self.data[self.offset:self.offset+maxSize]
        self.offset += maxSize
        return data
    
