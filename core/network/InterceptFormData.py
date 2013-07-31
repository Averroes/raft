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
import sys
from PyQt4.QtCore import QTimer, SIGNAL, QObject, QIODevice

class InterceptFormData(QIODevice):
    def __init__(self, ioDevice):
        QIODevice.__init__(self, ioDevice.parent())
        self.ioDevice = ioDevice
        self.__data = b''

        self.open(self.ReadOnly)
        self.setOpenMode(self.ioDevice.openMode())

    def get_intercepted_data(self):
        return self.__data

    def __getattr__(self, name):
        ret = getattr(self.ioDevice, name)
        return ret

    def abort(self):
        self.ioDevice.abort()

    def isSequential(self):
        isseq = self.ioDevice.isSequential()
        return isseq

    def bytesAvailable(self):
        available = self.ioDevice.bytesAvailable()
        return available

    def readData(self, maxSize):
        data = self.ioDevice.read(maxSize)
        if data:
            self.__data += data
        return data

