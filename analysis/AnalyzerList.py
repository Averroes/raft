#
# Analyzer list
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

import pkgutil
import inspect
import sys

import analysis.analyzers

class AnalyzerList():

    def __init__(self, framework):
        self.framework = framework
        self.analyzerlist = None

    def find_analyzers(self):
        """Returns a list of all analyzer class objects found in the analyzers folder"""
        #Import all submodles of analysis.analyzers
        package=analysis.analyzers
        analyzerclasses=[]
        
        #Walk the tree of packages and subpackages, importing each.
        #print 'Current Modules: %s'%sys.modules
        for importer, modname, ispkg in pkgutil.walk_packages(path=package.__path__,
                                                  prefix=package.__name__+'.'):
            #print(modname)
            #print "Found submodule %s (is a package: %s)" % (modname, ispkg)
            try:
                #print 'attempting to reload %s'%modname
                module=reload(sys.modules[modname])
                #print 'reloaded %s'%module
            except KeyError,e:
                module = __import__(modname, fromlist="junk")
                #print 'first time loaded %s'%module
            except ImportError,e:
                print 'IMPORT ERROR ON modname'
                print e
            
            #print "Imported", module
            classmembers = inspect.getmembers(module, inspect.isclass)
            #print classmembers
            #classmembers now has a list of tuples ( (classname, classobject), ...)
            
            #Pull out useful class objects into a new list for use later
            #Unfortunately our relative import of AbstractAnalyzer shows up, so filter it out.
            #TODO: Any better way to make AbstractAnalyzer not show up?  Seems like other imports could also show.
            for c in classmembers:
                if c[0] != 'AbstractAnalyzer':
                    analyzerclasses.append(c[1])
        #print 'Final List of Analyzers: %s'%(analyzerclasses,)
        
        return analyzerclasses

    def instantiate_analyzers(self, analyzerclasses=None, reset=True, useallanalyzers=False):
        """Find all analyzers and initialize objects for them if not already existing.
           If analyzerclasses is supplied, instantiate those, 
                otherwise, look up the available analyzers in the filesystem and use those. 
           If reset==True, dump existing analyzers and recreate"""
        
        if self.analyzerlist==None or reset:
            analyzerstoinstantiate=self.find_analyzers() if analyzerclasses is None else analyzerclasses
            self.analyzerlist=list()
            for analyzerclass in analyzerstoinstantiate:  #analyzerlist=[x() for x in ]
                analyzerinstance=analyzerclass()
                
                isenabledstring=self.framework.get_config_value('ANALYSISENABLED',str(analyzerinstance.__class__))
                #would rather use the bool return type from get_config_value, but it coerces "not found" to False
                analyzerinstance.isenabled=False if isenabledstring == 'False' else True
                
                if analyzerinstance.isenabled or useallanalyzers:
                    self.analyzerlist.append(analyzerinstance)
                    config=self.framework.get_config_value('ANALYSIS',str(analyzerinstance.__class__))
                    if config:
                        analyzerinstance.setConfiguration(config)
                

    def __iter__(self):
        return iter(self.analyzerlist)

