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
from PyQt4.QtCore import (Qt, SIGNAL, pyqtSignature, QUrl, QSettings, QDir, QThread)
from PyQt4.QtGui import *

def populate_tree_widget(treewidget,treedict):
    """
    Populates a qt tree widget from a nested dictionary.
    
    "Leaves" of the dictionary can be of 3 types:
     - A basic python type understandable by Qt (string, bool, etc.)
     - a 2-tuple, in which case the first item is considered editable.
        The other item is attached to the widget as "customdata", and can then be referenced later.
        (for example, a reference to the analyzer object could be stored, letting you access its contents later.)
     - a function returning a widget.  This widget will be used directly in the tree at the appropriate spot.
    
    """
    
    #newwidget=QTreeWidget()
    #newwidget.setColumnCount(2)
    #newwidget.setHeaderLabels(["Setting","Value"])
    
    #Priming recursion
    currentsrcnode=treedict
    currentdestnode=treewidget
    
    recursive_generate_tree_widget_helper(currentsrcnode,currentdestnode)
    
    #return newwidget
    
def recursive_generate_tree_widget_helper(currentsrcnode, currentdestnode):
    """Recursive helper for generate_tree_widget.  You probably want to call generate_tree_widget"""
    
    #print type(currentsrcnode)
    #print currentsrcnode
    #print type(currentdestnode)
    #print currentdestnode
    try:
        #print "----------------------"
        #print currentsrcnode
        #print currentdestnode
        for key in currentsrcnode.keys():
            tempitem=QTreeWidgetItem(currentdestnode)
            tempitem.setText(0,str(key))
            tempitem.setFlags(Qt.ItemIsEditable|Qt.ItemIsEnabled|Qt.ItemIsSelectable)
            recursive_generate_tree_widget_helper(currentsrcnode[key],tempitem)
            
    except AttributeError:
        #Not a dictionary.  Add as a value ("leaf")

        #check the type to see if it's a tuple (store special value), a function (call it),
        #or none of the above (Assume it's a basic Qt-compatible obj, Qt should throw if not.
        currenttype=type(currentsrcnode)

        #TODO: Consider replacing line below to handle subtypes,etc of list and tuple...
        #Essentially anything capable of having a length of 2, but isn't a string or dict
        #ought to be valid input, but isn't currently (has to be an actual basic tuple or list)
        if currenttype == tuple or currenttype == list:
            if ( type(currentsrcnode[0]) is bool ):
                if currentsrcnode[0] == True:
                    #print "True!"
                    currentdestnode.setCheckState(1,Qt.Checked)
                else:
                    #print "currentsrcnode: %s" % str(currentsrcnode[0])
                    currentdestnode.setCheckState(1,Qt.Unchecked)
                currentdestnode.setFlags(Qt.ItemIsUserCheckable|Qt.ItemIsEnabled|Qt.ItemIsEditable)
            else:
                currentdestnode.setData(1,Qt.EditRole, currentsrcnode[0])
            currentdestnode.customdata=currentsrcnode[1]
            
        
        elif callable(currentsrcnode):
            currentdestnode=currentsrcnode()
        
        else:
            currentdestnode.setData(1, Qt.EditRole, currentsrcnode)
            #currentdestnode.setFlags(Qt.ItemIsEditable|Qt.ItemIsEnabled|Qt.ItemIsSelectable)
        
            
def obj_list_to_dict(objlist, valueattr=None):
    """
    Changes a list of objects into a dictionary organized by package.
    Output is suitable for use with generate_tree_widget()
    """
    
    outdict={}
    #print objlist
    for x in objlist:
        #Create a list of all parent packages.
        #exclude first two (so root becomes analyzers folder)
        packagelist=list(x.__module__.split('.')[2:])

        #This used to be needed to remove duplicates, but it appears to not be needed now?
        #if packagelist[-1]==x.__class__.__name__:
        #    packagelist.pop()
        
        itemvalue=getattr(x,valueattr) if valueattr is not None else True
            
        recursive_lists_to_nested_dict(packagelist,outdict,value=itemvalue,customdata=x)

    #print outdict
    return outdict
    
def recursive_lists_to_nested_dict(list, dictionary, value=None, customdata=None):
    """
        Adds a list of pathing information (such as a full path, package name, etc)
        to a hierarchial dictionary recursively.
        
        Assumes the pathing information has already been tokenized, separators removed, and
        put into list.
        
        dictionary: what the pathing info will be added to.
        
        If both value and customdata are None, this function excepts.
        
        If customdata is set, a 2-tuple is created for the "leaf" of the dictionary for this call.
        Value is placed in the 0th position, and customdata is placed in the last position.
        
        If customdata is not set, value is placed directly as the value of the last item in the
        dictionary.
    """
        

    if len(list) > 1:
        #print list
        #print dictionary
        branch = dictionary.setdefault(list[0], {})
        recursive_lists_to_nested_dict(list[1:], branch, value, customdata)
    else:
        #print list
        if customdata==None:
            dictionary[list[0]] = value
        else:
            dictionary[list[0]] = (value,customdata)

def tree_widget_to_dict(treewidget):
    """Inverse of generate_tree_widget"""
    
    newdict={}
    
    rootnode=treewidget.invisibleRootItem()
    
    if rootnode.childCount()==0:
        return newdict
    
    recursive_tree_widget_to_dict_helper(rootnode,newdict)

    #We used the invisible root item to make the recursion easier, but now we need to strip it back out.
    return newdict['']
    

    
def recursive_tree_widget_to_dict_helper(treenode,dictnode):

    numbranches=treenode.childCount()
    
    if numbranches > 0:
        for i in range(numbranches):
            #create dict node at this level
            currentname=str(treenode.text(0))
            branch = dictnode.setdefault(currentname, {})
            
            #recursive call for children
            recursive_tree_widget_to_dict_helper(treenode.child(i), branch)
            
    else:
        #If no children, leaf, set data
        currentname=str(treenode.text(0))
        treedata=treenode.data(1,Qt.EditRole)
            
        try:
            customdata=treenode.customdata
        except AttributeError:
            #No custom data was defined, just a regular node
            dictnode[currentname]=str(treedata.toString())
        else:
            #custom data found, make a tuple in the dict
            dictnode[currentname]=(str(treedata.toString()), customdata)
        
    
    
    
    
    