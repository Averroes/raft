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

from .resultsclasses import AnalysisRun
from .resultsclasses import AnalysisResults
from .resultsclasses import ResultSet
from .resultsclasses import SingleResult

class ResultFactory(object):
    
    def __init__(self):
        pass
    
    def loadClassByName(self,fqcn):
        module,dot,classname = fqcn.rpartition('.')
        #print("module: "+module)
        loadedmodule=__import__(module,globals(),locals(),[classname,], 0)
        loadedclass=getattr(loadedmodule,classname)
        #print "factory says:",loadedclass
        return loadedclass
    
    def createItems(self, requesterclass, itemid ,db ,cursor):
        #print "requesterclass:",requesterclass
        #print "requesterclass.type:",requesterclass.__class__
        #print "itemid:",itemid
        if isinstance(requesterclass,AnalysisRun.AnalysisRun):
            return self.createItemsAnalysisRun(requesterclass, itemid ,db ,cursor)
        elif isinstance(requesterclass,AnalysisResults.AnalysisResults):
            return self.createItemsAnalysisResults(requesterclass, itemid ,db ,cursor)
        elif isinstance(requesterclass,ResultSet.ResultSet):
            return self.createItemsResultSet(requesterclass, itemid ,db ,cursor)
        elif isinstance(requesterclass,SingleResult.SingleResult):
            return self.createItemsSingleResult(requesterclass, itemid ,db ,cursor)
        else:
            raise Exception('unsupported instance type %s' % (type(requesterclass)))

    def createItemsAnalysisRun(self, requesterclass, itemid ,db ,cursor):
        #print "Starting createItemsAnalysisRun"
        returnlist=list() 
        for instance in db.analysis_get_instances_per_run(cursor, itemid):
                classtype=instance[4]
                #print "class field from DB:",classtype
                loadedclass=self.loadClassByName(classtype)
                #print "loadedclass:",loadedclass
                tempAR=loadedclass(resultfactory=self)
                instanceid=instance[0]
                tempAR.instanceid=instanceid
                tempAR.dbgenerated=True
                tempAR.dbretrieved=False
                tempAR.setAnalyzerInfo(instance[2],instance[1], instance[3])
                tempAR.numresults=instance[5]
                returnlist.append(tempAR)
        return returnlist
    
    def createItemsAnalysisResults(self, requesterclass, itemid ,db ,cursor):
        
        overall={}
        pages={}
        nofindings={}
        
        resultcounts={'Overall':0,'Page':0,'No':0}
        
        
        #print "Starting createItemsAnalysisResults"
        resultsets=db.analysis_get_resultsets_per_instance(cursor,itemid)
        for resultset in resultsets:
            classtype=resultset[4]
            #print "class field from DB:",classtype
            loadedclass=self.loadClassByName(classtype)
            #print "loadedclass:",loadedclass
            numresults=resultset[5]
            if resultset[2]:
                store=overall
                storekey=resultset[3]
                resultcounts['Overall']+=numresults
                tempRS=loadedclass(storekey,None,True,resultfactory=self)
    
            elif numresults>0:
                store=pages
                storekey=resultset[1]
                resultcounts['Page']+=numresults
                tempRS=loadedclass(resultset[3],storekey,False,resultfactory=self)
            
            else:
                store=nofindings
                storekey=resultset[1]
                tempRS=loadedclass(resultset[3],storekey,False,resultfactory=self)
            
                
            tempRS.dbgenerated=True
            tempRS.dbretrieved=False
            tempRS.resultsetid=resultset[0]
            tempRS.numresults=resultset[5]
            store[storekey]=tempRS
            
        return resultcounts, overall, pages, nofindings
        
    def createItemsResultSet(self, requesterclass, itemid ,db ,cursor):
        #print "Starting createItemsResultSet"
        
        results=list()
        stats={}
        
        dbresults=db.analysis_get_singleresults_per_resultset(cursor,itemid)
        for result in dbresults:
            classtype=result[8]
            #print "Factory:READ class field from DB:",classtype
            loadedclass=self.loadClassByName(classtype)
            #print "Factory:createItemsResultSet:loadedclass:",loadedclass
            
            span= None if result[6] is None else (result[6],result[7]) 
            try:
                data= ast.literal_eval(result[5])
            except:
                data = result[5]
            tempresult=loadedclass(result[3],result[4],data, span, result[1], result[2], resultfactory=self)
            results.append(tempresult)
        
        dbstats=db.analysis_get_stats_per_resultset(cursor,itemid)
        for stat in dbstats:
            #AnalysisStat_ID, statName, statValue
            stats[stat[1]]=stat[2]
        
        return results,stats
            
    def createItemsSingleResult(self, requesterclass, itemid ,db ,cursor):
        pass
    
    
                
