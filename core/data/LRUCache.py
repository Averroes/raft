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

class LRUCache():
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.offset = 0
        self.lru = []
        [self.lru.append('') for i in range(0, maxsize)]
        self.cache = {}

    def has_key(self, key):
        return key in self.cache

    def getitem(self, key):
        return self.cache[key]

    def setitem(self, key, value):
        if key not in self.cache:
            size = len(self.cache)
            if size > self.maxsize:
                k = self.lru[self.offset]
                self.cache.pop(k)
            self.lru[self.offset] = key
        self.cache[key] = value

