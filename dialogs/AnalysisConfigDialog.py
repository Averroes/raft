#
# Analysis Config dialog
#
# Authors: 
#          Justin Engler
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

from PyQt4.QtCore import (Qt, SIGNAL, QObject)
from PyQt4.QtGui import *

from utility import TreeWidgetTools
from ui import AnalysisConfig

class AnalysisConfigDialog(QDialog, AnalysisConfig.Ui_analysisConfigDialog):
    """ The Analysis Config Dialog """
    
    def __init__(self, framework, parent=None):
        super(AnalysisConfigDialog, self).__init__(parent)
        self.setupUi(self)
        self.framework = framework
        self.analyzerobj=None
        #self.analyzerConfig=None
        
    def viewItemSelected(self, index):
        selecteditem=self.analyzerList.itemFromIndex(index)
        
        #Don't do much if it's not a leaf node in the tree
        if selecteditem.childCount()==0:
            self.analyzerobj=selecteditem.customdata
            self.selecteditem=selecteditem
            self.analyzerDesc.setText(self.analyzerobj.generalInfoToHTML())
            
            #Attempt to read config for selected analyzer from the db
            configdata=self.framework.get_config_value('ANALYSIS',str(self.analyzerobj.__class__))
            #print "read after analyzer click: %s"%configdata
            
            if configdata is not None and len(configdata)>0:
                self.analyzerobj.setConfiguration(configdata)
            
            rootitem = self.analyzerConfig.invisibleRootItem()
            if rootitem.childCount() > 0:
                self.deleteChildren(rootitem)
                #while self.analyzerConfig.topLevelItemCount > 0:
                #    self.analyzerConfig.removeItemWidget(self.analyzerConfig.headerItem(),1)
            #self.verticalLayoutTopRight.removeWidget(self.analyzerConfig)
                
            self.analyzerobj.generateConfigurationGui(self.analyzerConfig)
            #generatedwidget=self.analyzerobj.generateConfigurationGui()
            
            #generatedwidget.setParent(self.RightWidget)
            #self.verticalLayoutTopRight.addWidget(generatedwidget)
            #generatedwidget.setExpandsOnDoubleClick(False)
            #self.analyzerConfig=generatedwidget
            #self.analyzerConfig.show()
    def deleteChildren(self,selecteditem):
        numbranches=selecteditem.childCount()
        if numbranches > 0:
            for i in range(numbranches):
                child = selecteditem.child(0)
                self.deleteChildren(child)
                selecteditem.removeChild(child)
                del child
            
    def closeButtonClicked(self):
        #print "CLOSE"
        self.close()
    
    def saveButtonClicked(self):
        #print "SAVE"
        if self.analyzerobj is not None:
            newsettings=TreeWidgetTools.tree_widget_to_dict(self.analyzerConfig)
            #print self.analyzerobj
            
            
            self.framework.set_config_value('ANALYSIS',str(self.analyzerobj.__class__),
                                                     self.analyzerobj.encodeConfiguration(newsettings))
            #print newsettings, newsettings.__class__ 
            self.analyzerobj.setConfiguration(newsettings)
            
            checked = False
            if self.selecteditem.checkState(1) == Qt.Checked:
                checked = True
            self.framework.set_config_value('ANALYSISENABLED',str(self.analyzerobj.__class__),checked)


    def saveAllAnalyzerSettings(self):
        #TODO:  Add stuff for saving settings, not just enable/disable
        
        rootitem=self.analyzerList.invisibleRootItem()
        
        self.recursiveSaveSettings(rootitem)
        

    
    def recursiveSaveSettings(self,rootitem):
        
        childcount=rootitem.childCount()
        
        for i in range(childcount):
            currentchild=rootitem.child(i)
            if hasattr(currentchild,'customdata'):
                checked = False
                if currentchild.checkState(1) == Qt.Checked:
                    checked = True
                self.framework.set_config_value('ANALYSISENABLED',str(currentchild.customdata.__class__),checked)
                
            self.recursiveSaveSettings(currentchild)
            

        
    def addnodeButtonClicked(self):
        """
        If the addnode button is clicked, copy the currently selected node and insert it back into the tree.
        """
        
        #Don't do anything if there's nothing to do
        if self.analyzerConfig is None or len(self.analyzerConfig.selectedItems())==0:
            return
        
        selecteditems=self.analyzerConfig.selectedItems()
        copiedvalues={}
        #print selecteditems[0].parent()
        TreeWidgetTools.recursive_tree_widget_to_dict_helper(selecteditems[0],copiedvalues)
        #Pull original keys out of copiedvalues so the changes don't interfere with the loop
        tempkeylist=tuple(copiedvalues.keys())
        for key in tempkeylist:
            copiedvalues['COPY OF '+key]=copiedvalues[key]
            del copiedvalues[key]
        
        #if the parent is None, that means we're copying a rootish-level item.  Use the invisible root to add to
        virtualparent=selecteditems[0].parent() if selecteditems[0].parent() is not None else self.analyzerConfig.invisibleRootItem()
        
        #add the copied dictionary to the tree
        TreeWidgetTools.recursive_generate_tree_widget_helper(copiedvalues,virtualparent)
        
        
    def delnodeButtonClicked(self):
        #Don't do anything if there's nothing to do
        if self.analyzerConfig is None or len(self.analyzerConfig.selectedItems())==0:
            return
        
        selecteditem=self.analyzerConfig.selectedItems()[0]
        
        #if the parent is None, that means we're removing a rootish-level item.  Use the invisible root to remove from
        virtualparent=selecteditem.parent() if selecteditem.parent() is not None else self.analyzerConfig.invisibleRootItem()
        virtualparent.removeChild(selecteditem)
        del selecteditem
            
    def defaultsButtonClicked(self):
        self.framework.clear_config_value("ANALYSIS")
        self.framework.clear_config_value("ANALYSISENABLED")

    def saveAllButtonClicked(self):
        self.saveAllAnalyzerSettings()
        
            
