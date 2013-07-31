#
# Factory to create new HeadlessWebPages
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

from PyQt4.QtCore import QObject, SIGNAL

from HeadlessWebPage import HeadlessWebPage

class HeadlessPageFactory(QObject):
    class Logger:
        def __init__(self):
            pass
        def log(self, msg):
            # TODO: direct to console
            print(msg)

    def __init__(self, framework, context, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework
        self.context = context
        self.logger = HeadlessPageFactory.Logger()

    def new_page(self, parent = None):
        return HeadlessWebPage(self.framework, self.logger, parent)
