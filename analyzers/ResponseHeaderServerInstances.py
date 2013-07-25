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


from analysis.AbstractAnalyzer import AbstractAnalyzer
import re

class ResponseHeaderServerInstances(AbstractAnalyzer):
    
    def __init__(self):
        self.desc = "Detect instances of Web servers based on response headers"
        self.friendlyname = "Response Headers Server Instances"
        self.unique_server_headers = {}
        self.re_server_pattern = re.compile(b'^Server:\s*(.+)$', re.I)
        
    def preanalysis(self):
        pass

    def analyzeTransaction(self, target, results):

        responseHeaders = target.responseHeaders
        url = target.responseUrl
        for line in responseHeaders.splitlines():
            m = self.re_server_pattern.match(line)
            if m:
                server_value = m.group(1).rstrip()
                if server_value not in self.unique_server_headers:
                    self.unique_server_headers[server_value] = [url]
                else:
                    if url not in self.unique_server_headers[server_value]:
                        self.unique_server_headers[server_value].append(url)

    def postanalysis(self,results):
        keys = list(self.unique_server_headers.keys())
        keys.sort()

        # TODO: add support for some sort of summary
        # results.addSummaryResult(
        #     context = 'Summary',
        #     type = '',
        #     desc = '',
        #     data = ['<hr>'+'<br>'.join(keys)+'<hr>']
        #     )

        for server_value in keys:
            results.addOverallResult(
                                    context = server_value,
                                    type = '',
                                    desc = server_value,
                                    data = ['<hr>'+'<br>'.join(self.unique_server_headers[server_value])+'<hr>'],
                                    span = None ,               #This is the first character and last character where the finding was detected.
                                                                     #None is ok here too if it's not pinpointable.
                                    severity = 'Informational',  #High, Medium, Low, or make your own
                                    certainty = 'High' #High, Medium, Low, or make your own
                                        )
        
    def getDefaultConfiguration(self):
        return {}
        
        
        
        
