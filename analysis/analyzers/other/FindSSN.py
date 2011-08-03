#
# Author: Justin Engler
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

from ...AbstractAnalyzer import AbstractAnalyzer


class FindSSN(AbstractAnalyzer):
    
    def __init__(self):
        self.desc="Searches for SSNs or similarly-formatted ID numbers."\
        "  Uses a pattern defined in settings"
        self.friendlyname="Find SSNs"
        
    def preanalysis(self):
        self.SSNregex=re.compile(self.getCurrentConfiguration()["Search Pattern"], re.UNICODE|re.MULTILINE|re.DOTALL)

    def analyzeTransaction(self, target, results):
        responsedata=target.responseBody
        for found in self.SSNregex.finditer(responsedata):
            results.addPageResult(pageid=target.responseId,
                                  url=target.responseUrl,
                                  type='Sensitive Data',
                                  desc='A possible SSN (or similar identifier) was found.',
                                  data={'Number':found.group()},
                                  span=found.span())
            
            
    def getDefaultConfiguration(self):
        return {"Search Pattern":"\d{3}-\d{2}-\d{4}"}
        
        
        
        