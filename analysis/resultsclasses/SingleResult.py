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

from PyQt4.QtGui import *
from PyQt4.QtCore import Qt
            
class SingleResult(object):
    """defines a a single finding/result"""
    
    #Constants and string translation.
    #TODO: There has to be a better way to do this.
    UNKNOWN=None
    HIGH=1000
    MEDIUM=100
    LOW=10
    
    SEVERITYNAME={None:'Undefined', 1000:'High', 100: 'Medium', 10:'Low'}
    
    def __init__(self, type, desc, data, span=None, severity=UNKNOWN, certainty=UNKNOWN, resultfactory=None, highlightdata=None):
        """type=general type of result.
            desc=friendly description of result
            data=any associated data for the result
            span=the starting and ending string indexes where the problem was found in the response
            severity=One of the constants UNKNOWN, HIGH, MEDIUM, LOW
            certainty=One of the constants UNKNOWN, HIGH,MEDIUM, LOW
            """
        
        self.severity=severity
        self.certainty=certainty
        self.type=type
        self.desc=desc
        self.data=data
        self.span=span
        self.resultfactory=resultfactory
        if highlightdata is not None:
            self.data['highlightdata']=highlightdata
            
    def toHTML(self):
        
        locationtext=''
        dataoutput=''
        if self.span is not None:
            locationtext='%s to %s'%self.span
        
        # TODO: This is still f'd up.  Look at 7/27 --Seth
        #try: 
        #datalist = ast.literal_eval(self.data)
        dataoutput = '<ol><li>%s</li></ol>' % self.data
        #for k in datalist:
        #   dataoutput += "<li>%s: %s</li>" % (k,datalist[k])
        #dataoutput += '</ol>'
        #except ValueError:
        #    print "ValueError: %s" % self.data
        #except:
        #    print "Error occurred on this data: %s" % self.data

        NiceOutput="""
        <h3>%s</h3><br>
        <font size="-1">Severity: <b>%s</b> | Certainty: <b>%s | Location: %s</b></font>
        <p><b>Description:</b>
        <ul>
         <li>%s</li>
        </ul>
        <p><b>More Details:</b>
        <li>
         <ul>%s</ul>
        </li>
        """%(self.type,
               SingleResult.SEVERITYNAME[self.severity] if self.severity in SingleResult.SEVERITYNAME else self.severity,
               SingleResult.SEVERITYNAME[self.certainty] if self.certainty in SingleResult.SEVERITYNAME else self.certainty, #SEVERITYNAME is not a typo
               locationtext,
               self.desc,
               dataoutput)
                
        return NiceOutput
    
    def generateTreeItem(self,parentnode):
        tempitem=QTreeWidgetItem(parentnode)
        tempitem.setText(0,str(self.type))
        tempitem.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
        tempitem.customdata=self
        return tempitem
    
    def generateTreeChildren(self,db,cursor,parentnode):
        return
    
    def getFoundData(self):
        """If you 
        """
        return self.data['highlightdata'] if 'highlightdata' in self.data else None
    
    
    
