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

class TemplateItem(object):
    T_NONE = 0
    T_TEXT = 1
#    T_PARAMETER = 2
    T_BUILTIN = 3
    T_PAYLOAD = 4
    T_FUNCTION = 5

    def __init__(self, item_value, item_type):
        self.item_value = item_value
        self.item_type = item_type
        self.items = []

    def append(self, item):
        self.items.append(item)

    def __repr__(self):
        return 'TemplateItem(%s, %s, %s)' % (repr(self.item_value), repr(self.item_type), repr(self.items))

    def is_text(self):
        return self.item_type == self.T_TEXT

    def is_parameter(self):
        return self.item_type == self.T_PAYLOAD or self.item_type == self.T_BUILTIN

    def is_payload(self):
        return self.item_type == self.T_PAYLOAD

    def is_builtin(self):
        return self.item_type == self.T_BUILTIN

    def is_function(self):
        return self.item_type == self.T_FUNCTION



