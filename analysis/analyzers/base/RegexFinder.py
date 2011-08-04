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

from ...AbstractAnalyzer import AbstractAnalyzer




class RegexFinder(AbstractAnalyzer):
        
    def __init__(self):
        self.desc="Searches for user specified regular expressions within responses."
        self.friendlyname="Regex Finder" 
    
    def preanalysis(self):

        currconfig=self.getCurrentConfiguration()
        
        self.regex=dict(currconfig)
        
    def analyzeTransaction(self, target, results):
        responseBody=target.responseBody
        
        for main,sub in self.regex.items():
            for regexName,regexValue in sub.items():
                compiledRegex = re.compile(regexValue)
                for found in compiledRegex.finditer(responseBody):
                    founddata=found.group(1)
                    results.addPageResult(pageid=target.responseId, 
                                  url=target.responseUrl,
                                  type='Regex Found: %s - %s'%(main,regexName),
                                  desc='A regex from the custom regex list was matched.',
                                  data={'found':founddata},
                                  span=found.span(),
                                  highlightdata=founddata)
                   
    def getDefaultConfiguration(self):
        return defaultconfig
    
    
    
    
#Strings for default config
defaultconfig=\
{
    'Private Information':
        {
            'SSN': '\D(\d{3}\-{0,1}\d{2}\-{0,1}\d{4})\D',
            'US Phone Number': '\D(\({0,1}\d{3}\){0,1}-{0,1}\d{3}-{0,1}\d{4})\D',
            'Email Address': '([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4})'
        },
    'Credit Card Numbers':
        {
            'Mastercard': '(5[1-5]\d{2}(-{0,1}\s{0,1}\d{4}){3})',
            'Amex': '(3[4,7]\d{2}-{0,1}\s{0,1}\d{6}-{0,1}\s{0,1}\d{5})',
            'Diners Club': '(0[0-5][68][0-9][0-9]{11})',
            'JCB Card': '((2131|1800|35\d{3})\d{11})',
            'Discover': '(6011(-{0,1}\s{0,1}\d{4}){3})'
        },
    'JavaScript':
        {
            'Location Setting': '(\.location\s*=|\.href\s*=)',
            'innerHTML': '(\.innerHTML)',
            'Document Write':'(document\.write\(|document\.writeln\()',
            'Eval':'(eval\()'
        }
}