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
import json
from .resultsclasses import AnalysisResults
from utility import TreeWidgetTools
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt


class AbstractAnalyzer(object):
    """
    AbstractAnalyzer
    Defines the interface for a RAFT analyzer.
    
    Analyzers search through request or response data,
    locate items of interest, and report back the details
    
    Analyzers shall either inherit from AbstractAnalyzer
    or implement all of the member functions with compatible
    signatures and return values.
    
    Each analyzer will be instantiated before analysis begins, and each
    resulting analysis object will be reused on each page.
    It is the responsibility of the analyzer writer to save or clear
    object fields as desired for each page.
    """
    
    #####################Standard Functions
    #####################Override when defining your own analyzers
    def __init__(self):
        self.desc="Did you define a desc in your subclass? "\
              "An abstract class to define what an analyzer must support."\
              "  Automatically called during analysis or configuration start."
        self.friendlyname="Abstract Analyzer"
        self.currentconfiguration=None    
        
        
        
    def preanalysis(self):
        """Any special pre-test setup goes here.  This will be called after configuration, before any pages are loaded
        """
        pass
    
    def analyzeTransaction(self,transaction,results):
        """
        Performs an analysis on target. This function must be defined by a subclass.
        Transaction is information about the request and response (the target of your analysis)
        """
        raise Exception("analyze() must be defined in a subclass for analysis")
    
    
    def postanalysis(self,results):
        """Any post-test steps go here.  Called after all pages were analyzed."""
        pass

    def getDefaultConfiguration(self):
        """Returns the default configuration dictionary for this analyzer.
           If your module is configurable at all, you must override this."""
        return {}

    def defaultEnabled(self):
        """Returns if the analyzer should be Enabled by default"""
        return True
    
    #####################Special Functions
    #####################You shouldn't need to override these unless you're doing something very special
        
    def setConfiguration(self,newconfiguration):
        """Accepts any configuration data from the system.
            Either a settings dictionary or a JSON string representation
            of the same is OK."""
        if (type(newconfiguration)==str or type(newconfiguration)==str) and len(newconfiguration)>0:
            #print "FOUND JSON, decoding"
            #pprint.pprint(newconfiguration)
            temp=json.loads(newconfiguration)
            self.currentconfiguration = temp
            
        elif type(newconfiguration)==dict:
            #print "FOUND DICT"
            self.currentconfiguration = newconfiguration
        else:
            raise ValueError("I don't know what that configuration is.")
        #pprint.pprint(self.currentconfiguration)
        return self.currentconfiguration
    
    def encodeConfiguration(self,newconfiguration):
        """Takes a given configuration and encodes it for storage.
            Does not alter existing runtime config of this analyzer.
        """
        return json.dumps(newconfiguration)
        
        
        
    def initResultsData(self):
        """Sets up results data.  Called after preanalysis, but before actual analysis.
        Analyzer writers shouldn't need to override this function except for special cases, like
        when subclassing a custom AnalysisResults object.
        """
        self.analysisresults=AnalysisResults.AnalysisResults()
        self.analysisresults.setAnalyzerInfo(self.desc,self.friendlyname,str(self.__class__).translate('<>'))
        
        
    def getResults(self):
        """returns a reference to the Analyzer's results collection.
        Analyzer writers shouldn't need to override this function"""
        return self.analysisresults
    
    
    def getCurrentConfiguration(self):
        """Returns the current config dict.  Should not need to override this"""
        
        if not hasattr(self,'currentconfiguration') or self.currentconfiguration is None:
            self.currentconfiguration=self.getDefaultConfiguration()
            #print 'Using Default Config'
        return self.currentconfiguration
        
        
    def generateConfigurationGui(self,analyzerConfig):
        currentconfig=self.getCurrentConfiguration()
        
        TreeWidgetTools.populate_tree_widget(analyzerConfig,currentconfig)
        
        
    def generalInfoToHTML(self):
        """Returns an HTML 'header' string describing the analyzer"""
        outstring="""<h1>%s</h1>
        (%s)
        <p>%s</p>
        """%(self.friendlyname,str(self.__class__).translate('<>'),self.desc)
        return outstring
    
