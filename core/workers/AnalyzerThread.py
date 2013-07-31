#
# Analyer thread
#
# Authors: 
#          Justin Engler
#          Seth Law
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

import inspect

from PyQt4.QtCore import Qt, QObject, SIGNAL, QThread, QTimer, QMutex, QString

from cStringIO import StringIO

from analysis.AnalyzerList import AnalyzerList
from core.database.constants import ResponsesTable

class AnalyzerThread(QThread):
    def __init__(self, framework, parent = None):
        QThread.__init__(self, parent)
        self.framework = framework

        self.callback_object = None
        self.qtimer = QTimer()
        self.qlock = QMutex()
        QObject.connect(self, SIGNAL('quit()'), self.handle_quit)
        QObject.connect(self, SIGNAL('started()'), self.handle_started)

        self.Data = None
        self.read_cursor = None
        self.cursor = None

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.read_cursor = self.Data.allocate_thread_cursor()
        self.cursor = self.Data.allocate_thread_cursor()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.read_cursor:
            self.read_cursor.close()
            self.Data.release_thread_cursor(self.read_cursor)
            self.read_cursor = None
        if self.cursor:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def run(self):
        QObject.connect(self, SIGNAL('do_runAnalysis()'), self.handle_runAnalysis, Qt.DirectConnection)
        self.exec_()

    def runAnalysis(self, callback_object):
        self.callback_object = callback_object
        QTimer.singleShot(50, self, SIGNAL('do_runAnalysis()'))

    def handle_quit(self):
        self.framework.debug_log('AnalyzerThread quit...')
        self.close_cursor()
        self.exit(0)

    def handle_started(self):
        self.framework.debug_log('AnalyzerThread started...')
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def handle_runAnalysis(self):
        fullanalysistext = ''
        if not self.qlock.tryLock():
            self.framework.debug_log('failed to acquire lock for analyzers')
        else:
            try:
                fullanalysistext = self.analyze_content()
            except Exception, e:
                self.framework.report_exception(e)
            finally:
                self.qlock.unlock()

        if self.callback_object:
            self.callback_object.emit(SIGNAL('runAnalysisFinished(QString)'), str(fullanalysistext))

    def result_type_to_string(self,resulttype):
        """Reads type and package information from a result, and returns it as a string"""
        resultclass=resulttype.__class__
        return "".join((resultclass.__module__,".",resultclass.__name__))
        
    def analyze_content(self):
        """ Perform analysis on the captured content"""

        #TODO:  NEW DB THREAD TO HOLD RESPONSES, ANOTHER FOR WRITING RESULTS
        scopeController = self.framework.getScopeController()
        response = self.Data.read_all_responses(self.read_cursor)
        response_IDs = []
        for row in response:
            dbrow = [m or '' for m in row]
            Id = dbrow[ResponsesTable.ID]
            url = dbrow[ResponsesTable.URL]
            if scopeController.isUrlInScope(url, url):
                response_IDs.append(Id)
            
        #Instantiate all found analyzers
        analyzerobjects = AnalyzerList(self.framework)
        analyzerobjects.instantiate_analyzers()
        
        analysisrunid=self.Data.analysis_start(self.cursor)
        
        #TODO - Consider threading from here down

        for x in analyzerobjects:
            
            #dbconfig=self.Data.get_config_value(self.read_cursor, 'ANALYSIS', str(x.__class__))
            #print "dbconfig=%s"%dbconfig
            #print "class=%s"%x.__class__
            #x.setConfiguration(dbconfig)
            x.preanalysis()
            x.initResultsData()
            resultinstance=x.getResults()
            x.analyzerinstanceid=self.Data.analysis_add_analyzer_instance(self.cursor, 
                                                                          analysisrunid,
                                                                          str(x.__class__).translate(None,'<>'),
                                                                          x.friendlyname,x.desc, self.result_type_to_string(resultinstance))     
        
        fullanalysistext=StringIO()

        for Id in response_IDs:
            transaction = self.framework.get_request_response(Id)
            for analyzer in analyzerobjects:
                try:
                    
                    analyzer.analyzeTransaction(transaction,analyzer.getResults())
                    tempanalysisresults=analyzer.getResults()
                    
                    
                    #If there were results for this page, add them to the DB
                    if transaction.responseId in tempanalysisresults.pages:
                        pageresultset=self.Data.analysis_add_resultset(self.cursor, analyzer.analyzerinstanceid,
                                                                       transaction.responseId,False,transaction.responseUrl,
                                                                       self.result_type_to_string(tempanalysisresults.pages[transaction.responseId]))
                        for result in tempanalysisresults.pages[transaction.responseId].results:
                            self.Data.analysis_add_singleresult(self.cursor, 
                                                                pageresultset,
                                                                result.severity,
                                                                result.certainty,
                                                                result.type,
                                                                result.desc,
                                                                #TODO: Consider db structure to handle data field
                                                                str(result.data),
                                                                result.span,
                                                                self.result_type_to_string(result))
                        for key,value in tempanalysisresults.pages[transaction.responseId].stats.items():
                            self.Data.analysis_add_stat(self.cursor, pageresultset, key, value)
                except Exception, e:
                    # TODO: add real debugging support
                    self.framework.debug_log(transaction)
                    self.framework.report_exception(e)
                    
        #Post Analysis
        for analyzer in analyzerobjects:
                results=analyzer.getResults()
                analyzer.postanalysis(results)
                
                for context in results.overall.keys():
                    
                    overallresultset=self.Data.analysis_add_resultset(self.cursor, 
                                                                      analyzer.analyzerinstanceid,
                                                                      None,True,context,
                                                                      self.result_type_to_string(results.overall[context]))
                    for result in results.overall[context].results:
                        self.Data.analysis_add_singleresult(self.cursor, 
                                                            overallresultset,
                                                            result.severity,
                                                            result.certainty,
                                                            result.type,
                                                            result.desc,
                                                            #TODO: Consider db structure to handle data field
                                                            str(result.data),
                                                            result.span,
                                                            self.result_type_to_string(result))
                        #print "WRITING:",self.result_type_to_string(result)
                    for key,value in results.overall[context].stats.items():
                        self.Data.analysis_add_stat(self.cursor, overallresultset, key, value)
                
        self.Data.commit()
        #Output results to analysis tab
        #for analyzer in analyzerobjects:
            #fullanalysistext.write(analyzer.getResults().toHTML())

        return ''

    
    
