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

from analysis.AbstractAnalyzer import AbstractAnalyzer

class StringFinder(AbstractAnalyzer):
        
    def __init__(self):
        self.desc="Searches for static strings in files."
        self.friendlyname="Find Strings" 
    
    def preanalysis(self):

        currconfig=self.getCurrentConfiguration()
        
        self.searchstrings=dict(currconfig)
        
    def analyzeTransaction(self, target, results):
        """TODO:  This is really slow.  Consider one of the following instead if it gets unbearable:
            https://hkn.eecs.berkeley.edu/~dyoo/python/ahocorasick/
            https://github.com/axiak/pyre2
            http://code.google.com/p/esmre/
        """
        
        responsedata=target.responseBody
        
        for stringtype,stringlist in self.searchstrings.items():
            for ident,searchstring in stringlist.items():
                startindex=responsedata.find(str(searchstring))
       
                if startindex > -1:
                    endindex=startindex+len(searchstring)
                    founddata=responsedata[startindex:endindex]
                    results.addPageResult(pageid=target.responseId, 
                                          url=target.responseUrl,
                                          type='String Found: %s - %s'%(stringtype,ident),
                                          desc='A string from the find strings list was matched.',
                                          data={'found':founddata},
                                          span=(startindex,endindex),
                                          highlightdata=founddata)
                   
    def getDefaultConfiguration(self):
        
        return defaultconfig
    
    
    
    
#Strings for default config
defaultconfig=\
{'Error Messages': {1: 'A syntax error has occurred',
                    2: 'ADODB.Field error',
                    3: 'ASP.NET is configured to show verbose error messages',
                    4: 'ASP.NET_SessionId',
                    5: 'Active Server Pages error',
                    6: 'An illegal character has been found in the statement',
                    7: 'An unexpected token "END-OF-STATEMENT" was found',
                    8: 'CLI Driver',
                    9: "Can't connect to local",
                    10: 'Custom Error Message',
                    11: 'DB2 Driver',
                    12: 'DB2 Error',
                    13: 'DB2 ODBC',
                    14: 'Died at',
                    15: 'Disallowed Parent Path',
                    16: 'Error Diagnostic Information',
                    17: 'Error Message : Error loading required libraries.',
                    18: 'Error Report',
                    19: 'Error converting data type varchar to numeric',
                    20: 'Fatal error',
                    21: 'Incorrect syntax near',
                    22: 'Index of',
                    23: 'Internal Server Error',
                    24: 'Invalid Path Character',
                    25: 'Invalid procedure call or argument',
                    26: 'Invision Power Board Database Error',
                    27: 'JDBC Driver',
                    28: 'JDBC Error',
                    29: 'JDBC MySQL',
                    30: 'JDBC Oracle',
                    31: 'JDBC SQL',
                    32: 'Microsoft OLE DB Provider for ODBC Drivers',
                    33: 'Microsoft VBScript compilation error',
                    34: 'Microsoft VBScript error',
                    35: 'MySQL Driver',
                    36: 'MySQL Error',
                    37: 'MySQL ODBC',
                    38: 'ODBC DB2',
                    39: 'ODBC Driver',
                    40: 'ODBC Error',
                    41: 'ODBC Microsoft Access',
                    42: 'ODBC Oracle',
                    43: 'ODBC SQL',
                    44: 'ODBC SQL Server',
                    45: 'OLE/DB provider returned message',
                    46: 'ORA-0',
                    47: 'ORA-1',
                    48: 'Oracle DB2',
                    49: 'Oracle Driver',
                    50: 'Oracle Error',
                    51: 'Oracle ODBC',
                    52: 'PHP Error',
                    53: 'PHP Parse error',
                    54: 'PHP Warning',
                    55: 'Parent Directory',
                    56: "Permission denied: 'GetObject'",
                    57: 'PostgreSQL query failed: ERROR: parser: parse error',
                    58: 'SQL Server Driver][SQL Server',
                    59: 'SQL command not properly ended',
                    60: 'SQLException',
                    61: 'Supplied argument is not a valid PostgreSQL result',
                    62: 'Syntax error in query expression',
                    63: 'The error occurred in',
                    64: 'The script whose uid is',
                    65: 'Type mismatch',
                    66: 'Unable to jump to row',
                    67: 'Unclosed quotation mark before the character string',
                    68: 'Unterminated string constant',
                    69: 'Warning: Cannot modify header information - headers already sent',
                    70: 'Warning: Supplied argument is not a valid File-Handle resource in',
                    71: 'Warning: mysql_query()',
                    72: 'Warning: pg_connect(): Unable to connect to PostgreSQL server: FATAL',
                    73: 'You have an error in your SQL syntax near',
                    74: 'data source=',
                    75: 'detected an internal error [IBM][CLI Driver][DB2/6000]',
                    76: 'error',
                    77: 'include_path',
                    78: 'invalid query',
                    79: 'is not allowed to access',
                    80: 'missing expression',
                    81: 'mySQL error with query',
                    82: 'mysql error',
                    83: 'on MySQL result index',
                    84: 'on line',
                    85: 'server at',
                    86: 'server object error',
                    87: 'supplied argument is not a valid MySQL result resource',
                    88: 'unexpected end of SQL command'},
 'Local Storage Detected': {'HTML5 Local Storage':'localStorage',
                            'dojox multiplatform storage library':'dojox.storage',
                            'Web SQL Database Object':'openDatabase',
                            'Web SQL Database Execute':'executeSql'},
 'Other Strings': {'Test': 'Test'}}
