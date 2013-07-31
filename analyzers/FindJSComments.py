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

from analysis.AbstractAnalyzer import AbstractAnalyzer


class FindJSComments(AbstractAnalyzer):
    
    #Class variables shared across all instances
    JSSingleLineCommentRegex = re.compile(b"\s+(//.*)")
    JSMultiLineCommentRegex = re.compile(b"(/\*.*?\*/)",re.M|re.DOTALL)
    ContentTypeRegex = re.compile("html|javascript|css",re.I)
    
    def __init__(self):
        self.desc="Searches for JavaScript Comments."
        self.friendlyname="Find JavaScript Comments"  
    
    def analyzeTransaction(self, target, results):
        
        if self.ContentTypeRegex.search(target.responseContentType):
            
            responsedata=target.responseBody
        
            
            for found in FindJSComments.JSSingleLineCommentRegex.finditer(responsedata):
                #print "Found JS comment: " + found.group(1)    
                results.addPageResult(pageid=target.responseId, 
                                  url=target.responseUrl,
                                  type='Sensitive Data',
                                  desc='JavaScript Comment was found.',
                                  data={'JavaScript Comment':found.group(1)},
                                  span=found.span(),
                                  highlightdata=found.group(1))
                
            for found in FindJSComments.JSMultiLineCommentRegex.finditer(responsedata):
                #print "Found JS comment: " + found.group(1)
                results.addPageResult(pageid=target.responseId, 
                                  url=target.responseUrl,
                                  type='Sensitive Data',
                                  desc='JavaScript Comment was found.',
                                  data={'JavaScript Comment':found.group(1)},
                                  span=found.span(),
                                  highlightdata=found.group(1))
        
