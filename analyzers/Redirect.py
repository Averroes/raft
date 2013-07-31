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
import urllib.request, urllib.error, urllib.parse

from analysis.AbstractAnalyzer import AbstractAnalyzer


class Redirect(AbstractAnalyzer):
    
    #Class variables shared across all instances
    data = {}
    LocationRegex = re.compile(b'Location:\s+(\S+)',re.I)
    
    
    def __init__(self):
        self.desc="Analyzes HTTP Redirects for abnormalities"
        self.friendlyname="Redirect Analyzer"
    
    def analyzeTransaction(self, target, results):
        status = target.responseStatus
        host = target.requestHost
        if (target.responseStatus == "302"):
            m = self.LocationRegex.search(target.responseHeaders)
            if ( m != None ):
                redirectLocation = m.group(1)
                for k,val in target.requestParams.items():
                    v = urllib.parse.unquote(val)
                    matched = False
                    if redirectLocation in v:
                        matched = True
                    elif urllib.parse.quote(redirectLocation) in v:
                        matched = True
                    elif urllib.parse.unquote(redirectLocation) in v:
                        matched = True
                    if matched:
                        results.addPageResult(pageid=target.responseId, 
                                url=target.responseUrl,
                                type=self.friendlyname,
                                desc="Check the listed parameter for a possible open redirect",
                                data={'Possible Unvalidated Redirect':k},
                                span=m.span(),
                                highlightdata=val)