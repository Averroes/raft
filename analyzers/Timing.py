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
import pprint
import time

from analysis.AbstractAnalyzer import AbstractAnalyzer


class Timing(AbstractAnalyzer):
    
    #Class variables shared across all instances
    ResponseDateRegex = re.compile(b"Date:\ (.*)")
    #ReqDateRegex matching format: Mon Jul  4 23:55:11 2011 GMT
    ReqDateRegex = re.compile("\w{3}\s\w{3}\s+\d+\s\d\d:\d\d:\d\d\s\d{4}\s\w{3}")
    URLRegex = re.compile("\/\/(.*?)(\/.*)$")
    hosts = {}
    
    
    def __init__(self):
        self.desc="Request/Response Timing Analysis (Potential DoS finder)."
        self.friendlyname="Timing Analysis"
    
    def analyzeTransaction(self, target, results):
        responseheaders=target.responseHeaders
        url = target.responseUrl

        elapsedtime = None
        if ( target.requestTime != ''):
            elapsedtime = int(target.requestTime)
        else:
            # Response Date Format
            # Mon, 13 Jun 2011 16:16:09 GMT
            # %a, %d %b %Y %H:%M:%S %Z
            # Request Date Format
            # Mon Jun 13 10:16:40 2011
            # %a %b %d %H:%M:%S %Y
            # Another format: ERROR REQDATE: Mon Jul  4 23:55:11 2011 GMT
            reqdate=target.requestDate
            try:
                m = Timing.ReqDateRegex.search(reqdate)
                if (m != None):
                   requestdate = time.strptime(reqdate,"%a %b  %d %H:%M:%S %Y %Z")
                else:
                   requestdate = time.strptime(reqdate, '%a %b %d %H:%M:%S %Y')
            except ValueError:
                print("ERROR REQDATE: %s" % reqdate)
                # TODO: fix this
                return
            responsedate = None
            m = Timing.ResponseDateRegex.search(responseheaders)
            if (m != None):
                restemp = m.group(1).rstrip()
                resdate = restemp.decode('utf-8')
                try:
                    responsedate = time.strptime(resdate, '%a, %d %b %Y %H:%M:%S %Z')
                except ValueError:
                    print("ERROR RESPONSEDATE: %s" % responsedate)
        
            if (responsedate != None):
                elapsedtime = abs(time.mktime(responsedate) - time.mktime(requestdate))
        
        m2 = Timing.URLRegex.search(url)
        if (m2 != None and elapsedtime != None):
            host = m2.group(1)
            path = m2.group(2)
            try:
                self.hosts[host]
            except:
                self.hosts[host] = {}
                self.hosts[host]['count'] = 0
                self.hosts[host]['times'] = []
                self.hosts[host]['total'] = 0
                self.hosts[host]['min'] = elapsedtime
                self.hosts[host]['max'] = elapsedtime
            
            self.hosts[host]['count'] +=1
            self.hosts[host]['total'] += elapsedtime
            self.hosts[host]['times'].append(elapsedtime)
            
            if (elapsedtime < self.hosts[host]['min']):
                self.hosts[host]['min'] = elapsedtime
            if (elapsedtime > self.hosts[host]['max']):
                self.hosts[host]['max'] = elapsedtime
                
            try:
                self.hosts[host][path] 
            except:
                self.hosts[host][path] = {}
                self.hosts[host][path]['count'] = 0
                self.hosts[host][path]['times'] = []
                self.hosts[host][path]['total'] = 0
                self.hosts[host][path]['min'] = elapsedtime
                self.hosts[host][path]['max'] = elapsedtime
            
            self.hosts[host][path]['count'] += 1
            self.hosts[host][path]['total'] += elapsedtime
            self.hosts[host][path]['times'].append(elapsedtime)
            

            if (elapsedtime < self.hosts[host][path]['min']):
                self.hosts[host][path]['min'] = elapsedtime
            if (elapsedtime > self.hosts[host][path]['max']):
                self.hosts[host][path]['max'] = elapsedtime
                    
    def postanalysis(self,results):
        header = "<table border='1'><tr><td align='center' width=200><b>HOST</b></td><td align='center' width=100><b>REQUESTS</b></td><td align='center' width=100><b>MIN</b></td><td align='center' width=100><b>MAX</b></td><td align='center' width=100><b>AVE</b></td></tr>"
        tail = "</table>"
        for h in self.hosts.keys():
            host = self.hosts[h]
            output = "<tr><td align='left'>%s</td><td align='right'>%d</td><td align='right'>%d</td><td align='right'>%d</td><td align='right'>%5d</td></tr>" % (h,host['count'],host['min'], host['max'], host['total']/host['count'])
            # def addOverallResult(self, type, desc, data, span=None, severity=None, certainty=None, context=None):
            results.addOverallResult(type=self.friendlyname,
                                     desc=self.desc,
                                     data={h:header + output + tail},
                                     span=None,
                                     certainty=None,
                                     context=h
                                     )
        
        
