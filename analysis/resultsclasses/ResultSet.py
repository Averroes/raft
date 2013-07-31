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

import ast

from .SingleResult import SingleResult
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

class ResultSet(object):
    """defines a group of related findings/results (ex. all findings for a page)"""
    
    def __init__(self, context, pageid, isoverall,resultfactory=None):
        self.results=list()
        self.stats={}
        self.context=context
        self.pageid=pageid
        self.isoverall=isoverall
        self.resultfactory=resultfactory
        
    def addResult(self,singleresult):
        self.results.append(singleresult)
        self.stats['count']=len(self.results)
    
    def toHTML(self):
        """
        Outputs the results to HTML for viewing in the GUI or reports.
        Override for custom reporting/display functionality
        """
        statsoutput=''
        resultsoutput=''
        
        for key,value in list(self.stats.items()):
            statsoutput+="<em>%s</em>: %s"%(key,value)
        
        resultcounter=1
        for result in self.results:
            resultsoutput+="<hr><h5>Result %s</h5><br>"%(resultcounter,)
            resultcounter+=1
            resultsoutput+=result.toHTML()

        return """
        <h3>%s%s</h3>
        <h4>Analysis Stats</h4>
        %s
        <h4>Results</h4>
        %s
        
        """%(('%s - '%(self.pageid) if self.pageid is not None else ''),
             self.context,
             statsoutput,
             resultsoutput)
        
    def generateTreeItem(self,parentnode):
        tempitem=QTreeWidgetItem(parentnode)
        #context, pageid, isoverall
        if self.isoverall:
            tempitem.setText(0,str(self.context))
        else:
            tempitem.setText(0,'%s: %s'%(self.pageid,self.context))
        tempitem.setText(1,'%s results'%self.numresults)
        tempitem.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
        tempitem.customdata=self
        return tempitem
    
    def generateTreeChildren(self,db,cursor,parentnode):
        if self.resultfactory is not None:
            factoryitems=self.resultfactory.createItems(self, self.resultsetid,db,cursor)
            resultset, stats = factoryitems
            for tempresult in resultset:
                self.results.append(tempresult)
            self.stats=stats               
        else:        
            #If this tree item came from the db, and we haven't populated it yet, populate it.
            if self.dbgenerated and not self.dbretrieved:
                dbresults=db.analysis_get_singleresults_per_resultset(cursor,self.resultsetid)
                
                for result in dbresults:
                    span= None if result[6] is None else (result[6],result[7]) 
                    data= ast.literal_eval(result[5])
                    tempresult=SingleResult(result[3],result[4],data, span, result[1], result[2])
                    self.results.append(tempresult)
                
                dbstats=db.analysis_get_stats_per_resultset(cursor,self.resultsetid)
                for stat in dbstats:
                    #AnalysisStat_ID, statName, statValue
                    self.stats[stat[1]]=stat[2]
                self.dbretrieved=True
        
        #Data is populated, make the treeitems
        for result in self.results:
            result.generateTreeItem(parentnode)
            
