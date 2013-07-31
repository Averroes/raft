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

class RaftDbCapture():
    def __init__(self, framework, Data, cursor, Id):
        row = Data.read_responses_by_id(cursor, Id)
        if row:
            dbrow = [m or '' for m in row]
            self.origin = str(dbrow[ResponsesTable.DATA_ORIGIN])
            self.host = str(dbrow[ResponsesTable.REQ_HOST])
            self.hostip = str(dbrow[ResponsesTable.HOST_IP])
            self.url = str(dbrow[ResponsesTable.URL])
            self.status = str(dbrow[ResponsesTable.STATUS])
            self.datetime = str(dbrow[ResponsesTable.REQDATE])
            self.method = str(dbrow[ResponsesTable.REQ_METHOD])
            self.content_type = str(dbrow[ResponsesTable.RES_CONTENT_TYPE])
            self.request_headers = str(dbrow[ResponsesTable.REQ_HEADERS])
            self.request_body = str(dbrow[ResponsesTable.REQ_DATA])
            self.response_headers = str(dbrow[ResponsesTable.RES_HEADERS])
            self.response_body = str(dbrow[ResponsesTable.RES_DATA])
            self.content_length = str(dbrow[ResponsesTable.RES_LENGTH])
            self.elapsed = str(dbrow[ResponsesTable.REQTIME])
            self.notes = str(dbrow[ResponsesTable.NOTES])
            self.confirmed = str(dbrow[ResponsesTable.CONFIRMED])
        else:
            raise Exception('unrecognized Id=%s' % (Id))

