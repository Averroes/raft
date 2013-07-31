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

from core.database.constants import ResponsesTable
from actions import interface

class RaftDbCapture():
    def __init__(self):
        pass
    def populate_by_id(self, framework, Data, cursor, Id):
        row = Data.read_responses_by_id(cursor, Id)
        if row:
            self.populate_by_dbrow(row)
        else:
            raise Exception('unrecognized Id=%s' % (Id))

    def populate_by_dbrow(self, row):
        responseItems = interface.data_row_to_response_items(row)
        self.origin = responseItems[ResponsesTable.DATA_ORIGIN]
        self.host = responseItems[ResponsesTable.REQ_HOST]
        self.hostip = responseItems[ResponsesTable.HOST_IP]
        self.url = responseItems[ResponsesTable.URL]
        self.status = responseItems[ResponsesTable.STATUS]
        self.datetime = responseItems[ResponsesTable.REQDATE]
        self.method = responseItems[ResponsesTable.REQ_METHOD]
        self.content_type = responseItems[ResponsesTable.RES_CONTENT_TYPE]
        self.request_headers = responseItems[ResponsesTable.REQ_HEADERS]
        self.request_body = responseItems[ResponsesTable.REQ_DATA]
        self.response_headers = responseItems[ResponsesTable.RES_HEADERS]
        self.response_body = responseItems[ResponsesTable.RES_DATA]
        self.content_length = responseItems[ResponsesTable.RES_LENGTH]
        self.elapsed = responseItems[ResponsesTable.REQTIME]
        self.notes = responseItems[ResponsesTable.NOTES]
        self.confirmed = responseItems[ResponsesTable.CONFIRMED]

