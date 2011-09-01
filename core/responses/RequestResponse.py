#
# This module supports the parsing and objectification of the HTTP Request/Response
#
# Authors: 
#          Seth Law (seth.w.law@gmail.com)
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

class RequestResponse(object):
    def __init__(self):
        self.Id = ''
        self.requestHeaders = ''
        self.requestBody = ''
        self.requestHost = ''
        self.requestHash = ''
        self.requestDate = ''
        self.requestTime = ''
        self.rawRequest = ''
        self.responseHeaders = ''
        self.responseBody=''
        self.responseStatus = ''
        self.responseHash = ''
        self.responseContentType = ''
        self.rawResponse = ''
        self.notes = ''
        self.confirmed = ''

        self.contentType = ''
        self.baseType = ''

        self.results = None
        

