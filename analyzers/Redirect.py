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

#import re

from analysis.AbstractAnalyzer import AbstractAnalyzer


class Redirect(AbstractAnalyzer):
    
    #Class variables shared across all instances
    data = {}
    
    
    def __init__(self):
        self.desc="Analyzes HTTP Redirects for abnormalities"
        self.friendlyname="Redirect Analyzer"
    
    def analyzeTransaction(self, target, results):
        status = target.responseStatus
        host = target.requestHost
        if (status == "302"):
            #print "Redirect Analysis engaged!"
            hash = target.responseHash
            try:
                self.data[host]
            except:
                self.data[host] = {}
            
            try:
                self.data[host][hash]
            except:
                self.data[host][hash] = {}
                self.data[host][hash]['data'] = target.responseBody
                self.data[host][hash]['count'] = 0
                
            self.data[host][hash]['count'] += 1

    def postanalysis(self,results):
        output = "The following redirect hashes were observed during analysis:\n"
        for host in self.data.iterkeys():
            output += " %s " % host
            for hash in self.data[host].iterkeys():
               output += "   %s  %10d" % (hash,self.data[host][hash]['count'])
               
            results.addOverallResult(type=self.friendlyname,
                                     desc=self.desc,
                                     data={host:output},
                                     span=(0,0),
                                     certainty=None,
                                     context=host
                                     )
