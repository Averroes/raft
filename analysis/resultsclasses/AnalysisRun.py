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

from AnalysisResults import AnalysisResults
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

class AnalysisRun(object):
    def __init__(self,timestamp=None, resultcount=None, resultfactory=None):
        self.timestamp=timestamp
        self.resultcount=resultcount
        self.analyzerlist=list()
        self.resultfactory=resultfactory
        
    def toHTML(self):
        
        outlist= [a.toHTML() for a in self.analyzerlist]
        
        return "".join(outlist)
    
    def generateTreeItem(self,parentnode):
        tempitem=QTreeWidgetItem(parentnode)
        tempitem.setText(0,str(self.timestamp))
        tempitem.setText(1,str(self.resultcount)+' results')
        tempitem.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
        tempitem.customdata=self
        return tempitem
    
    def generateTreeChildren(self,db,cursor,parentnode):
        if self.resultfactory is not None:
            for tempAR in self.resultfactory.createItems(self, self.runid,db,cursor):
                #print "tempAR returned:",tempAR
                self.analyzerlist.append(tempAR)
                tempAR.generateTreeItem(parentnode)
        else:
            for instance in db.analysis_get_instances_per_run(cursor, self.runid):
                instanceid=instance[0]
                tempAR=AnalysisResults()
                tempAR.instanceid=instanceid
                tempAR.dbgenerated=True
                tempAR.dbretrieved=False
                tempAR.setAnalyzerInfo(instance[2],instance[1], instance[3])
                tempAR.numresults=instance[5]

                self.analyzerlist.append(tempAR)
                tempAR.generateTreeItem(parentnode)