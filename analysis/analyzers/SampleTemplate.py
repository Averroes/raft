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


from analysis.AbstractAnalyzer import AbstractAnalyzer


class SampleTemplateClassName(AbstractAnalyzer):
    
    def __init__(self):
        self.desc="SampleTemplate Description."
        self.friendlyname="Sample Template Friendly Name"
        
    def preanalysis(self):
        #print "preanalysis: This function runs once at the start of analysis."
        #print "Delete this function if you don't have any preanalysis setup."
        pass

    def analyzeTransaction(self, target, results):
        #print "-------------------------------------------------------------------------------"
        #print "AnalyzeTransaction():"
        #print "This function gets run once per request/response pair to be analyzed."
        #print "We are now analyzing %s:%s"%(target.responseId,target.responseUrl)
        #print "You must define this function."
        #print "-------------------------------------------------------------------------------"
        #To  add a finding, call this (note the slight difference between this and the addOverallResult call below):
        results.addPageResult(pageid=target.responseId,
                                 url=target.responseUrl,
                                 type='Short Finding Name',
                                 desc='A longer description of the problemAlso, here are your config values: %s'%self.getCurrentConfiguration(),
                                 data={'somekey1':'somevalue1',
                                           'somekey2':1337},  #any base python type (list, dict, int, bool, str) works here
                                 span=(1337,31137), #This is the first character and last character where the finding was detected.
                                                                 #None is ok here too if it's not pinpointable.
                                 severity='SAMPLE: NOT A FINDING',  #High, Medium, Low, or make your own
                                 certainty='HIGH' #High, Medium, Low, or make your own
                                 )
        
        
    def postanalysis(self,results):
        #print "This function runs once after all request/response pairs were analyzed."
        #print "Define if it you need some sort of 'overall' analysis after your per-page analysis."
        #print "Delete it if you don't do that."
        #To  add a finding, call this (note the slight difference between this and the addPageResult call below):
        results.addOverallResult(
                                context="MyOverallResult",
                                type='Short Finding Name',
                                desc='A longer description of the problem.  Also, here are your config values: %s'%self.getCurrentConfiguration(),
                                data={'somekey1':'somevalue1',
                                               'somekey2':1337},  #any base python type (list, dict, int, bool, str) works here
                                span=None ,               #This is the first character and last character where the finding was detected.
                                                                 #None is ok here too if it's not pinpointable.
                                severity='SAMPLE: NOT A FINDING',  #High, Medium, Low, or make your own
                                certainty='HIGH' #High, Medium, Low, or make your own
                                    )
        
    def getDefaultConfiguration(self):
        #Any config values are defined here.  Users can change them in the Analysis Config section
        #To access the values, use self.getCurrentConfiguration(), which will return the dictionary with any
        #modifications made by the user in AnalysisConfig
        return {"Sample Configuration Key":"Sample Configuration Value"}
        
        
        
        
