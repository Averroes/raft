#
# Authors: 
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
import re

from ..AbstractAnalyzer import AbstractAnalyzer

class ASPNETApplicationServerErrors(AbstractAnalyzer):
    
    def __init__(self):
        self.desc = 'Find unique application instances based on server error'
        self.friendlyname = 'ASP.NET Application Server Error'

        self.re_server_error = re.compile(r'Server Error in \'(.*?)\' Application.')
        self.applications = {}
        self.all_urls = {}
    
    def analyzeTransaction(self, target, results):
        response_body =target.responseBody
        url = target.responseUrl

        m = self.re_server_error.search(response_body)
        if m:
            appname = m.group(1)
            if not self.applications.has_key(appname):
                self.applications[appname] = url
                self.all_urls[appname] = [url]
            else:
                if not url in self.all_urls[appname]:
                    self.all_urls[appname].append(url)
                if len(url) <= len(self.applications[appname]):
                    self.applications[appname] = url
                    
    def postanalysis(self,results):
        for appname, url in self.applications.iteritems():
            results.addOverallResult(self.friendlyname,
                                     desc = self.desc,
                                     data = self.all_urls[appname],
                                     span = None,
                                     certainty = None,
                                     context = 'Found %s -- %s' % (appname, url)
                                     )
        
