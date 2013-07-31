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

from .ResultSet import ResultSet
from .SingleResult import SingleResult
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

class AnalysisResults(object):
    """Contains all results found for a given analysis."""
    
    def __init__(self , resultfactory=None):
        """Results that span across multiple pages"""
        self.overall={}
        
        """Results that apply to a single page"""
        self.pages={} 
        
        """pages scanned with no results"""
        self.nofindings={}
        
        """counts of total results within each grouping"""
        self.resultcounts={'Overall':0,'Page':0,'No':0}
        
        self.desc=None
        self.friendlyname=None
        self.analyzerclass=None
        
        self.resultfactory=resultfactory
        
        
        
#############################Standard Functions
#############################Functions often used when writing an analyzer
    def addPageResult(self, pageid, url, type, desc, data, span=None, severity=None, certainty=None, highlightdata=None):
            """Adds a new per-page standard result to the given pageid for this analysis"""
            
            self.addCustomPageResult(pageid,
                                     SingleResult(type, desc, data, span, severity, certainty, highlightdata=highlightdata),url)
            
    def addOverallResult(self, type, desc, data, span=None, severity=None, certainty=None, context=None, highlightdata=None):
            """Adds a new overall result to this analysis"""
            self.addCustomOverallResult(SingleResult(type, desc, data, span, severity, certainty, highlightdata=highlightdata),context)
            
#############################Special Functions
#############################You shouldn't need to call these unless you're doing something crazy.
    def addCustomPageResult(self,pageid,result,url):
        if pageid not in self.pages:
            self.pages[pageid]=ResultSet(pageid,False,url)
        self.pages[pageid].addResult(result)
        
    def addCustomOverallResult(self,result,context):
        """Adds an arbitrary result object to the overall results."""
        if context not in self.overall:
            self.overall[context]=ResultSet(None,True,context)
        self.overall[context].addResult(result)
        
    def setAnalyzerInfo(self, newdesc,newfriendlyname, newanalyzerclass):
        self.desc=newdesc
        self.friendlyname=newfriendlyname
        self.analyzerclass=newanalyzerclass
        
        
    def toHTML(self):
        """returns an HTML representation of the entire analysis"""
        finaloutput=self.generalInfoToHTML()
        
        if len(self.overall) > 0:
            finaloutput+='<h2>Overall Results</h2>'
            for k in list(self.overall.keys()):
                finaloutput+=self.overall[k].toHTML()
                
               
        if len(self.pages)>0:
            finaloutput+='<h2>Results for each page analyzed</h2>'
            for k in list(self.pages.keys()):
                finaloutput+=self.pages[k].toHTML()
        return finaloutput
        
    def generalInfoToHTML(self):
        """Returns an HTML 'header' string describing the test performed"""
        outstring="""<h1>%s</h1>
                    <p>(%s)</p>
                    <p>%s</p>
                    """%(self.friendlyname,self.analyzerclass,self.desc)
        return outstring
        
    def generateTreeItem(self,parentnode):
        tempitem=QTreeWidgetItem(parentnode)
        tempitem.setText(0,str(self.friendlyname))
        tempitem.setText(1,"".join((str(self.numresults),' results')))
        tempitem.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
        tempitem.customdata=self
        return tempitem
    
    def generateTreeChildren(self,db,cursor,parentnode):
        if self.resultfactory is not None:
            factoryitems=self.resultfactory.createItems(self, self.instanceid,db,cursor)
            self.resultcounts, self.overall, self.pages, self.nofindings  = factoryitems
        else:
            #If this tree item came from the db, and we haven't populated it yet, populate it.
            if self.dbgenerated and not self.dbretrieved:
                resultsets=db.analysis_get_resultsets_per_instance(cursor,self.instanceid)
                for resultset in resultsets:
                    numresults=resultset[5]
                    if resultset[2]:
                        store=self.overall
                        storekey=resultset[3]
                        self.resultcounts['Overall']+=numresults
                        tempRS=ResultSet(storekey,None,True)
    
                    elif numresults>0:
                        store=self.pages
                        storekey=resultset[1]
                        self.resultcounts['Page']+=numresults
                        tempRS=ResultSet(resultset[3],storekey,False)
                    
                    else:
                        store=self.nofindings
                        storekey=resultset[1]
                        tempRS=ResultSet(resultset[3],storekey,False)
                    
                        
                    tempRS.dbgenerated=True
                    tempRS.dbretrieved=False
                    tempRS.resultsetid=resultset[0]
                    tempRS.numresults=resultset[5]
                    store[storekey]=tempRS
        self.dbretrieved=True
                
        #Now that the tree is populated, make the nodes
        childnodes=list()
        for name,store in (('Overall',self.overall),('Page',self.pages), ('No',self.nofindings)):
            storelen=len(store)
            if storelen>0:
                tempitem=QTreeWidgetItem(parentnode)
                tempitem.setText(0,'%s Results'%name)
                tempitem.setText(1,'%s results in %s set%s'%(self.resultcounts[name],str(storelen),'s' if storelen>1 else ''))
                tempitem.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                childnodes.append(tempitem)
                
                for k in store:
                    store[k].generateTreeItem(tempitem)

                

