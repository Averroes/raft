#
# This module supports the data model for spider queues
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

from core.data.DataTableDataModel import DataTableDataModel
from core.database.constants import SpiderQueueTable

class SpiderQueueDataModel(DataTableDataModel):

    ITEM_DEFINITION = (
            ('#', SpiderQueueTable.ID),
            ('Method', SpiderQueueTable.METHOD),
            ('URL', SpiderQueueTable.URL),
            ('Query Params', SpiderQueueTable.QUERY_PARAMS),
            ('Form Type', SpiderQueueTable.ENCODING_TYPE),
            ('Form Params', SpiderQueueTable.FORM_PARAMS),
            ('Referer', SpiderQueueTable.REFERER),
            ('Status', SpiderQueueTable.STATUS),
            )

    def __init__(self, framework, parent = None):
        DataTableDataModel.__init__(self, framework, SpiderQueueDataModel.ITEM_DEFINITION, parent)
