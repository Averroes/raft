#
# Author: Seth Law
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

import re
import urllib2

from ..AbstractAnalyzer import AbstractAnalyzer

class XSSFinder(AbstractAnalyzer):
    AlertRegex = re.compile("(alert\((.+?)\))",re.I)
    
    def __init__(self):
        self.desc="Identification of successful XSS attacks."
        self.friendlyname="XSS Finder"
    
    def analyzeTransaction(self, target, results):
        responseBody = target.responseBody
        rawRequest = target.rawRequest
        combined = None
        for found in self.AlertRegex.finditer(responseBody):
            if not combined:
                combined = target.requestHeaders + target.requestBody
            alert_data = found.group(2)
            matched = False
            if alert_data in combined:
                matched = True
            else:
                if urllib2.unquote(alert_data) in combined:
                    matched = True
            if matched:
                results.addPageResult(pageid=target.responseId, 
                                url=target.responseUrl,
                                type=self.friendlyname,
                                desc=self.desc,
                                data={'Javascript Alert found':found.group(1)},
                                span=found.span(),
                                highlightdata=found.group(1))
