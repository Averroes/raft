#
# This module supports the data model for the spider results
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
from core.database.constants import SpiderPendingAnalysisTable

class SpiderPendingAnalysisDataModel(DataTableDataModel):

    ITEM_DEFINITION = (
            ('#', SpiderPendingAnalysisTable.ID),
            ('Type', SpiderPendingAnalysisTable.ANALYSIS_TYPE),
            ('Url', SpiderPendingAnalysisTable.URL),
            ('Depth', SpiderPendingAnalysisTable.DEPTH),
            ('Content', SpiderPendingAnalysisTable.CONTENT),
            )

    def __init__(self, framework, parent = None):
        DataTableDataModel.__init__(self, framework, SpiderPendingAnalysisDataModel.ITEM_DEFINITION, parent)

