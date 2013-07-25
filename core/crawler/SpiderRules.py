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

from PyQt4.QtCore import Qt, QObject, SIGNAL, QUrl
from urllib import parse as urlparse

class SpiderRules(QObject):
    def __init__(self, framework, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework

        self.spiderConfig = self.framework.getSpiderConfig()

    def should_include_url(self, url, splitted = None):
        if splitted is None:
            splitted = urlparse.urlsplit(url)

        if self.spiderConfig.exclude_dangerous_paths:
            m = self.spiderConfig.re_dangerous_path.search(url)
            if m:
                return False

        if not self.spiderConfig.retrieve_media_files:
            components = splitted.path.split('/')
            for i in range(len(components)-1,-1,-1):
                component = components[i]
                if '.' in component:
                    extensions = (component.split('.'))[1:]
                    for ext in extensions:
                        if self.spiderConfig.re_media_extensions.match(extension):
                            return False

        return True
