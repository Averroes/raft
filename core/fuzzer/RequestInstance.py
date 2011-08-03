#
# instance of a request
#
# Authors: 
#          Gregory Fleischer (gfleischer@gmail.com)
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

from PyQt4.QtCore import (Qt, QObject, SIGNAL)

class RequestInstance(QObject):
    def __init__(self, method, url, headers, body, context, parent = None):
        QObject.__init__(self, parent)
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        self.context = context
        # mutable
        self.sequence_needed = False
        self.cancelled = False
        self.reqeust = None
        self.reply = None

    def __repr__(self):
        return ('<core.fuzzer.RequestInstance>: %s, %s, %s' % (self.method, self.url, self.context))

    def set_request_reply(self, requst, reply):
        self.request = request
        self.reply = reply

    def cancel(self):
        self.cancelled = True
        if self.reply:
            self.reply.abort()
