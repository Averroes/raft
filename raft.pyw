#!/usr/bin/env python
#
# RAFT - Response Analysis and Further Testing
#
# Authors: 
#          Nathan Hamiel
#          Gregory Fleischer (gfleischer@gmail.com)
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

import sys
import os
import shutil
import cgi
import re
import pprint
import traceback

#ToDo: Provide more detail in the try statements when modules are not found.
try:
    from PyQt4.QtCore import (Qt, SIGNAL, QObject, pyqtSignature, QSettings, QDir, QThread, QMutex, QDateTime, QString)
    from PyQt4.QtGui import *
    from PyQt4.QtNetwork import *
except:
    print("You need to have PyQT4 installed. Use your package manager to install it")
    sys.exit(1)

try:
    from PyQt4 import Qsci
except:
    print("You do not have QScintilla installed")
    sys.exit(1)

try:
    import lxml.html
except:
    print("You do not have lxml installed")
    sys.exit(1)

def add_thirdparty_path(basepath):
    thirdparty_libnames = ('pyamf', 'pdfminer',)
    thirdparty_search_path = os.path.join(basepath, 'thirdparty')
    for thirdparty_lib in thirdparty_libnames:
        # TODO: append at end of search path assuming that installed version take precedence??
        dirname = os.path.join(thirdparty_search_path, thirdparty_lib)
        if dirname not in sys.path:
            sys.path.append(dirname)

# use application executable path
executable_path = os.path.abspath(os.path.dirname(sys.argv[0]))
add_thirdparty_path(executable_path)

# use search path
basepath = sys.path[0]
if os.path.isfile(basepath):
    basepath = os.path.dirname(basepath)
add_thirdparty_path(basepath)

try:
    import pyamf.sol
except:
    print("You do not have a usable version of pyamf installed")
    sys.exit(1)

from sqlite3 import dbapi2 as sqlite
from lxml import etree

# Import UI components
from ui import RaftMain
from ui import RaftAbout

from dialogs.SearchDialog import SearchDialog
from dialogs.RequestResponseDetailDialog import RequestResponseDetailDialog
from dialogs.SequenceDialog import SequenceDialog
from dialogs.ProgressDialog import ProgressDialog
from dialogs.DiffDialog import DiffDialog
from dialogs.AnalysisConfigDialog import AnalysisConfigDialog
from dialogs.ConfigDialog import ConfigDialog
from dialogs.RaftBrowserDialog import RaftBrowserDialog
from dialogs.SimpleDialog import SimpleDialog

from tabs import VulnerabilitiesTab
from tabs import DataBankTab
from tabs import CookiesTab
from tabs import RequesterTab
from tabs import WebFuzzerTab
from tabs import DomFuzzerTab
from tabs import CrawlerTab
from tabs import ScopingTab

# Import actions
from actions import importers
from actions import request
from actions import interface
from actions import encoderlib
from actions import SettingsFiles

from core.database import database
from core.database.constants import ResponsesTable
from core.data import ScopeController
from core.crawler import SpiderConfig
from core.responses import RequestResponseFactory

# Import Analysis
from analysis.AnalyzerList import AnalyzerList
from analysis.resultsclasses.AnalysisRun import AnalysisRun
from analysis.ResultFactory import ResultFactory

# utility classes
from utility import TreeWidgetTools
from utility import WebFuzzer

from widgets.RequestResponseWidget import RequestResponseWidget
from widgets.ResponsesContextMenuWidget import ResponsesContextMenuWidget

from core.data import ResponsesDataModel, SiteMapModel
from core.data import DomFuzzerQueueDataModel
from core.data import DomFuzzerResultsDataModel
from core.data import SpiderQueueDataModel
from core.data import SpiderPendingResponsesDataModel
from core.data import SpiderPendingAnalysisDataModel
from core.data import SpiderInternalStateDataModel

from core.network.InMemoryCookieJar import InMemoryCookieJar
from core.network.DatabaseNetworkAccessManager import DatabaseNetworkAccessManager

from lib.extractors import BaseExtractor

from core.framework.Framework import Framework
from core.workers import SiteMapThread
from core.workers import SearchThread
from core.workers import DatabaseThread
from core.workers import ResponsesThread
from core.workers import ImporterThread
from core.workers import AnalyzerThread
from core.workers import DomFuzzerThread
from core.workers import SpiderThread

MAC = True
try:
    from PyQt4.QtGui import qt_mac_set_native_menubar
except ImportError:
    MAC = False
    
__version__ = "2011.7.14-alpha"
    
#ToDo: Create a global search through response content
#ToDo: Auto-Highlight error conditions

class RaftMain(QMainWindow, RaftMain.Ui_MainWindow):
    """ Reimplementation of the imported Ui_MainWindow class """
    def __init__(self, dbfilename = '', parent=None):
        super(RaftMain, self).__init__(parent)
        self.setupUi(self)
        if MAC:
            qt_mac_set_native_menubar(False)

        # hide currently unimplemented features
        self.reqTabRawRequestTab.hide()
        self.reqTabRawRequestTab.setParent(None)

        # default filename is temp.raftdb
        if dbfilename:
            self.dbfilename = dbfilename
        else:
            self.dbfilename = "temp.raftdb"

        # initialize framework
        self.framework = Framework(self)

        # restore settings
        self.restore_settings()

        # Create progress dialog
        self.Progress = ProgressDialog()

        # add helper and utility singletons
        # TODO: should be base extractor and that loads/returns appropriate type
        self.contentExtractor = BaseExtractor.BaseExtractor()
        self.framework.setContentExtractor(self.contentExtractor)

        # Create actions for items
        self.responsesDataTree.doubleClicked.connect(self.response_item_double_clicked)
        self.fillingDataTree = False
        # TODO: currentChanged no longer available 
        self.responsesDataTree.clicked.connect(self.fill_bottom)
        self.responsesDataTree.activated.connect(self.fill_bottom)
        # TODO: Setup sorting for the responsesDataTree.  The following enables the QTreeView for sorting, but doesn't actually work.
        #self.responsesDataTree.setSortingEnabled(True)
        
        #analysis tab connections
        self.mainAnalysisTreeWidget.clicked.connect(self.analysistree_handle_click)
        self.mainAnalysisTreeWidget.activated.connect(self.analysistree_handle_click)
        self.mainAnalysisTreeWidget.expanded.connect(self.analysistree_handle_expand)
        
        self.cookiesTabIndex = self.mainTabWidget.indexOf(self.tabMainCookies)
        self.mainTabWidget.currentChanged.connect(self.main_tab_change)
        
        # Toolbar buttons and actions
        self.actionButtonOpen.triggered.connect(self.open_file)
        self.actionZoomIn.triggered.connect(self.zoom_in)
        self.actionZoomOut.triggered.connect(self.zoom_out)
        self.actionDiff.triggered.connect(self.diff)
        self.actionAnalyze.triggered.connect(self.analyze_content)
        self.actionSequence.triggered.connect(self.display_sequence)
        self.actionConfig.triggered.connect(self.display_config)
        self.actionSearch.triggered.connect(self.display_search)
        self.actionBrowser.triggered.connect(self.launch_browser)
        
        self.encodeButton.clicked.connect(self.encode_data)
        self.encodeWrapButton.clicked.connect(self.encode_wrap)
        self.decodeButton.clicked.connect(self.decode_data)
        self.decodeWrapButton.clicked.connect(self.decode_wrap)
        
        # Create the actions for the buttons
        # self.connect(self.encodeButton, SIGNAL("clicked()"), self.encode_values)
        # self.connect(self.encodeWrapButton, SIGNAL("clicked()"), self.wrap_encode)
        # self.connect(self.decodeButton, SIGNAL("clicked()"), self.decode_values)
        # self.connect(self.decodeWrapButton, SIGNAL("clicked()"), self.wrap_decode)
        
        # Actions for Menus
        self.actionNew_Project.triggered.connect(self.new_project)
        self.actionOpen.triggered.connect(self.open_file)
        self.actionSave_As.triggered.connect(self.save_as)
        self.actionImport_RaftCaptureXml.triggered.connect(lambda x: self.import_raft('raft_capture_xml'))
        self.actionImport_BurpLog.triggered.connect(lambda x: self.import_burp('burp_log'))
        self.actionImport_BurpState.triggered.connect(lambda x: self.import_burp('burp_state'))
        self.actionImport_BurpXml.triggered.connect(lambda x: self.import_burp('burp_xml'))
        self.actionImport_WebScarab.triggered.connect(self.import_webscarab)
        self.actionImport_ParosMessages.triggered.connect(lambda x: self.import_paros('paros_message'))
        self.actionRefresh_Responses.triggered.connect(self.refresh_responses)
        self.actionExport_Settings.triggered.connect(self.export_settings)
        self.actionImport_Settings.triggered.connect(self.import_settings)

        self.actionEncoder_Decoder.triggered.connect(self.detach_encoder)

        # Actions for configuration
        self.actionConfiguration_BlackHoleNetwork.triggered.connect(lambda x: self.raft_config_toggle('black_hole_network', x))
        self.actionAbout_RAFT.triggered.connect(self.display_about)
        self.actionAnalysisConfiguration.triggered.connect(self.display_analysis_config)

        # Declare, but do not fill, list of analyzers
        self.analyzerlist = AnalyzerList(self.framework)

        self.setup_others()

    def db_attach(self):
        self.framework.debug_log('Database %s attached' % (self.db))
        self.cursor = self.Data.allocate_thread_cursor()

    def db_detach(self):
        self.framework.debug_log('Database %s detached' % (self.db))
        if self.Data:
            self.close_cursor()

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def do_db_connect(self):
        ###
        # Set up initial data connections for tools
        ###
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

        self.Progress.show()
        # Set initial temp.raftdb file for storage of imported data.
        self.Data = database.Db(__version__)
        self.db = self.dbfilename
        self.databaseThread = DatabaseThread.DatabaseThread(self.framework, self.Data, self)
        self.connect(self, SIGNAL('connectDbFinished()'), self.connectDbFinishedHandler, Qt.QueuedConnection)
        self.databaseThread.start()
        self.databaseThread.connectDb(self.db, self)

    def connectDbFinishedHandler(self):
        self.framework.setDB(self.Data, self.db)
        self.actionConfiguration_BlackHoleNetwork.setChecked(self.framework.get_raft_config_value('black_hole_network', bool))
        self.Progress.close()
        self.refresh_analysis_tab()

    def setup_others(self):

        # set request response factory
        self.framework.setRequestResponseFactory(RequestResponseFactory.RequestResponseFactory(self.framework, self))

        # scoping and spider
        self.framework.setScopeController(ScopeController.ScopeController(self.framework, self))
        self.framework.setSpiderConfig(SpiderConfig.SpiderConfig(self.framework, self))

        # setup network accessmanager
        self.dbNetworkAccessManager = DatabaseNetworkAccessManager(self.framework, self.framework.get_global_cookie_jar())
        self.framework.setNetworkAccessManager(self.dbNetworkAccessManager)

        # set up tabs
        self.vulnerabilitiesTab = VulnerabilitiesTab.VulnerabilitiesTab(self.framework, self)
        self.dataBankTab = DataBankTab.DataBankTab(self.framework, self)
        self.cookiesTab = CookiesTab.CookiesTab(self.framework, self)
        self.requesterTab = RequesterTab.RequesterTab(self.framework, self)
        self.webfuzzerTab = WebFuzzerTab.WebFuzzerTab(self.framework, self)
        self.domFuzzerTab = DomFuzzerTab.DomFuzzerTab(self.framework, self)
        self.crawlerTab = CrawlerTab.CrawlerTab(self.framework, self)
        self.scopingTab = ScopingTab.ScopingTab(self.framework, self)

        # sitemap
        self.siteMapRequestResponse = RequestResponseWidget(self.framework, self.sitemapTabPlaceholder, self.sitemapSearchControlPlaceholder, self)

        # TODO: cleanup site map and optimize...
        self.siteMapModel = SiteMapModel.SiteMapModel(self.framework)
        self.siteMapThread = SiteMapThread.SiteMapThread(self.framework, self.siteMapModel, self)
        self.siteMapThread.start(QThread.LowestPriority)

        self.importerThread = ImporterThread.ImporterThread(self.framework, self)
        self.connect(self, SIGNAL('runImportFinished()'), self.import_file_finished, Qt.QueuedConnection)
        self.importerThread.start(QThread.LowestPriority)

        self.treeViewSitemap.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeViewSitemapMenu = QMenu(self)
        treeViewSitemapCopyUrlAction = QAction("Copy URL", self)
        treeViewSitemapCopyUrlAction.triggered.connect(self.sitemap_copy_url)
        self.treeViewSitemapMenu.addAction(treeViewSitemapCopyUrlAction)

        self.connect(self.treeViewSitemap, SIGNAL('customContextMenuRequested(const QPoint &)'), self.sitemap_context_menu) 
        self.treeViewSitemap.activated.connect(self.siteMapRequestResponse.viewItemSelected)
        # TODO: clicked is annoying sometimes
        self.treeViewSitemap.clicked.connect(self.siteMapRequestResponse.viewItemSelected)
        self.treeViewSitemap.setModel(self.siteMapModel)

        # view tab
        self.viewTabRequestResponse = RequestResponseWidget(self.framework, self.responseTabPlaceholder, self.responseSearchControlPlaceholder, self)

        # Responses data
        self.responsesDataModel = ResponsesDataModel.ResponsesDataModel(self.framework, self)
        self.responsesDataTree.setModel(self.responsesDataModel)
        self.responsesThread = ResponsesThread.ResponsesThread(self.framework, self.responsesDataModel, self)
        self.responsesThread.start(QThread.LowPriority)
        self.connect(self, SIGNAL('fillResponsesFinished()'), self.fillResponsesFinishedHandler, Qt.QueuedConnection)
        self.responsesContextMenu = ResponsesContextMenuWidget(self.framework, self.responsesDataModel, self.responsesDataTree, self)

        #analysis results tab
        #add response widget to the bottom
        self.mainAnalysisTabRequestResponse = RequestResponseWidget(self.framework, self.mainAnalysisTabPlaceholder, self.mainAnalysisSearchControlPlaceholder, self)

        self.analyzerThread = AnalyzerThread.AnalyzerThread(self.framework, self)
        self.connect(self, SIGNAL('runAnalysisFinished(QString)'), self.handle_runAnalysisFinished, Qt.QueuedConnection)
        self.analyzerThread.start(QThread.LowestPriority)

        # dom fuzzer thread
        self.domFuzzerQueueDataModel = DomFuzzerQueueDataModel.DomFuzzerQueueDataModel(self.framework, self)
        self.domFuzzerFuzzQueueTable.setModel(self.domFuzzerQueueDataModel)
        self.domFuzzerResultsDataModel = DomFuzzerResultsDataModel.DomFuzzerResultsDataModel(self.framework, self)
        self.domFuzzerResultsTreeView.setModel(self.domFuzzerResultsDataModel)
        self.domFuzzerThread = DomFuzzerThread.DomFuzzerThread(self.framework, self.domFuzzerQueueDataModel, self.domFuzzerResultsDataModel,  self)
        self.domFuzzerThread.start(QThread.LowestPriority)
        self.domFuzzerTab.set_fuzzer_thread(self.domFuzzerThread)

        # spider thread
        self.spiderQueueDataModel = SpiderQueueDataModel.SpiderQueueDataModel(self.framework, self)
        self.crawlerSpiderQueueTreeView.setModel(self.spiderQueueDataModel)
        self.spiderPendingResponsesDataModel = SpiderPendingResponsesDataModel.SpiderPendingResponsesDataModel(self.framework, self)
        self.crawlerSpiderPendingResponsesTreeView.setModel(self.spiderPendingResponsesDataModel)
        self.spiderPendingAnalysisDataModel = SpiderPendingAnalysisDataModel.SpiderPendingAnalysisDataModel(self.framework, self)
        self.crawlerSpiderPendingAnalysisTreeView.setModel(self.spiderPendingAnalysisDataModel)
        self.spiderInternalStateDataModel = SpiderInternalStateDataModel.SpiderInternalStateDataModel(self.framework, self)
        self.crawlerSpiderInternalStateTreeView.setModel(self.spiderInternalStateDataModel)
        self.spiderThread = SpiderThread.SpiderThread(self.framework, self.spiderQueueDataModel, self.spiderPendingResponsesDataModel, self.spiderPendingAnalysisDataModel, self.spiderInternalStateDataModel, self)
        self.spiderThread.start(QThread.LowestPriority)
        self.crawlerTab.set_spider_thread(self.spiderThread)

        self.do_db_connect()

    def fillResponses(self, fillAll = False):
        self.Progress.show()
        self.fillingDataTree = True
        self.fillAll = fillAll
        self.responsesThread.fillResponses(fillAll, self)

    def fillResponsesFinishedHandler(self):
        self.Progress.close()
        self.fillingDataTree = False

        self.siteMapThread.populateSiteMap(self.fillAll)
        
    def restore_settings(self):
        # TODO: make constants make sense
        settings = QSettings('RaftDev', 'Raft');
        self.restoreGeometry(settings.value('RaftMain/geometry').toByteArray());

    def closeEvent(self, event):
        settings = QSettings('RaftDev', 'Raft');
        settings.setValue('RaftMain/geometry', self.saveGeometry());
        QWidget.closeEvent(self, event)

    def create_file(self):
        """ Open a dialog and allow for specifying a filename as well as creating a new database """
        
        file = QFileDialog.getSaveFileName(None, "Create File", "")
        self.Data.create_raft_db(str(file), __version__)

    def new_project(self):
        # Support '.raftdb' file types
        file = QFileDialog.getSaveFileName(None, "Create new RAFT DB file", "", "RAFT Database File (*.raftdb)")

        if file:
            self.Progress.show()
            try:
                # Reinitialize with the database value set from new db name
                self.framework.closeDB()

                # 2 seconds to settle
                QThread.sleep(2) 

                self.db = str(file)
                self.databaseThread.connectDb(self.db, self)
            finally:
                self.Progress.close()

    def open_file(self):
        """ Open File from file open dialog """
        
        file = QFileDialog.getOpenFileName(None, "Open file", "")
            
        if file != "":
            origdb = self.db
            self.Progress.show()
            # Reinitialize with the database value set
            self.framework.closeDB()
            self.db = str(file)
            self.databaseThread.connectDb(self.db, self)
        else:
            pass
        
    def save_as(self):
        """ Dialog and logic to save the temp.raftdb file to a working database """
        
        # Support '.db' file types
        file = QFileDialog.getSaveFileName(None, "Save to RAFT DB file", "", "RAFT Database File (*.raftdb)")

        if file:
            self.Progress.show()
            try:
                # Reinitialize with the database value set from new db name
                self.Progress.show()
                self.framework.closeDB()

                # 5 seconds to settle
                QThread.sleep(2) 

                # New db location
                new_db = str(file)
                shutil.move(self.db, new_db)
                self.db = new_db

                self.databaseThread.connectDb(self.db, self)
            finally:
                self.Progress.close()

    def refresh_responses(self):
        self.fillResponses(True)

    def export_settings(self):
        filename = QFileDialog.getSaveFileName(None, "Export RAFT Settings", "", "RAFT Settings File (*.raftsettings)")
        if filename:
            self.Progress.show()
            SettingsFiles.process_export(self.framework, filename)
            self.Progress.close()

    def import_settings(self):
        filename = QFileDialog.getOpenFileName(None, "Import RAFT Settings", "", "RAFT Settings File (*.raftsettings)")
        if filename:
            self.Progress.show()
            SettingsFiles.process_import(self.framework, filename)
            self.Progress.close()
        
    def import_file_finished(self):
        self.Progress.close()
        self.fillResponses()
        
    def import_proxy_file(self, proxy_file, source):
        self.Progress.show()
        self.importerThread.runImport(importers, proxy_file, source, self)

    def import_proxy_files(self, proxy_filelist, source):
        self.Progress.show()
        self.importerThread.runImportList(importers, proxy_filelist, source, self)

    def import_burp(self, source):
        """ Import a Burp proxy log """
        files = QFileDialog.getOpenFileNames(None, "Open file", "")
        if files is not None:
            self.import_proxy_files(files, source)

    def import_raft(self, source):
        """ Import a Raft Capture XML """
        files = QFileDialog.getOpenFileNames(None, "Open file", "")
        if files is not None:
            self.import_proxy_files(files, source)

    def import_webscarab(self, source):
        """ Import a WebScarab conversation log """

        # TODO: decide if there is a more friendly way to handle this
#        file = QFileDialog.getExistingDirectory(None, "Open saved conversation", "")
        file = QFileDialog.getOpenFileName(None, "Open saved conversation", "", "Converstation Log (conversationlog)")

        if file:
            self.import_proxy_file(str(file), 'webscarab')

    def import_paros(self, source):
        """ Import a Paros proxy log """
        
        file = QFileDialog.getOpenFileName(None, "Open file", "")

        if file:
            self.import_proxy_file(str(file), source)

################################################
# Is this section still being used now we are depend on the AnalyzerThread?  Can we rip it out?

    def analyze_content(self):
        """ Perform analysis on the captured content"""
        self.Progress.show()
        self.analyzerThread.runAnalysis(self)

    def handle_runAnalysisFinished(self, fullanalysistext = ''):
        self.Progress.close()
        #self.mainAnalysisEdit.setText(fullanalysistext)
        #self.refresh_analysis_tab()
        self.analysis_tab_add_results(None)

    def refresh_analysis_tab(self):
        self.runsdisplayed=list()
        
        rundata=self.Data.analysis_get_runs(self.cursor)
        self.populate_analysis_tree(rundata)
    
    def analysis_tab_add_results(self,results):
        rundata=self.Data.analysis_get_runs(self.cursor, lastx=1)
        self.populate_analysis_tree(rundata)
    
    def populate_analysis_tree(self,rundata):
        virtualparent=self.mainAnalysisTreeWidget.invisibleRootItem()
        resultfactory=ResultFactory()
        for run in rundata:
            runid=run[0]
            if runid not in self.runsdisplayed:
                self.runsdisplayed.append(runid)
                tempRun=AnalysisRun(run[1], run[2],resultfactory)
                tempRun.runid=runid
                tempRun.dbgenerated=True
                runtreeitem=tempRun.generateTreeItem(virtualparent)
                runtreeitem.customdata=tempRun
                tempRun.generateTreeChildren(self.Data,self.cursor,runtreeitem)

        
            
    def analysistree_handle_expand(self, index):
        item=self.mainAnalysisTreeWidget.itemFromIndex(index)
        item.wasexpanded=True
        self.analysistree_load_grandchildren(item)
                
    def analysistree_load_grandchildren(self, item):
        #For each child of this item:
        numchildren=item.childCount()
        for i in range(0,numchildren):
            childitem=item.child(i)
            childitem.wasexpanded=True
            #If the childitem doesn't have children, make them:
            if childitem.childCount()==0:
                childitem.customdata.generateTreeChildren(self.Data,self.cursor,childitem)
                childitem.wasexpanded=True

    def analysistree_handle_click(self, index):
        
        item=self.mainAnalysisTreeWidget.itemFromIndex(index)
        if hasattr(item,'customdata'):
            self.analysistree_load_decendants_to_bottom(item)
            self.mainAnalysisEdit.setText(item.customdata.toHTML())
        
            self.fill_analysis_request_response(item)
            
            if hasattr(item.customdata, 'getFoundData'):
                founddata=item.customdata.getFoundData()
                if founddata is not None:
                    self.set_analysis_request_response_highlight('response',founddata)

    def set_analysis_request_response_highlight(self, section, searchtext):
        self.mainAnalysisTabRequestResponse.set_search(section, searchtext)

    def analysistree_load_decendants_to_bottom(self,item):
        numchildren=item.childCount()
        if hasattr(item,'customdata') and numchildren==0: #(not hasattr(item,'wasexpanded') or not item.wasexpanded): 
            item.customdata.generateTreeChildren(self.Data, self.cursor, item)
            item.wasexpanded=True
        for i in range(0,numchildren):
            self.analysistree_load_decendants_to_bottom(item.child(i))
             
        

    def response_item_double_clicked(self, index):
        Id = interface.index_to_id(self.responsesDataModel, index)
        if Id:
            dialog = RequestResponseDetailDialog(self.framework, Id, self)
            dialog.show()
            dialog.exec_()

    def fill_bottom(self, index):
        """ Return the data from the database and fill bottom part of main window """
        if self.fillingDataTree:
            return
        Id = interface.index_to_id(self.responsesDataModel, index)
        if Id:
            self.viewTabRequestResponse.fill(str(Id))
    
    def fill_analysis_request_response(self, item):
        """ Return the data from the database and fill bottom part of main window """
        
        pageid=None

        for possible in (item, item.parent()):
            if hasattr(possible,"customdata") and hasattr(possible.customdata,"pageid"):
                    pageid=possible.customdata.pageid
                    break

        if pageid is not None:
            self.mainAnalysisTabRequestResponse.fill(str(pageid))
    
    ####
    # Requester tool section
    ####

    def main_tab_change(self):
        """ This function fires when the main tab widget changes. """
        
        position = self.mainTabWidget.currentIndex()
        
        if self.cookiesTabIndex == position:
            self.cookiesTab.fill_cookies_tab()
    
    ####
    # Web Fuzzer tool section
    ####
        
    def check_content_type(self, content):
        """ Check the content type of submitted content """
        
        # TODO: improve these to match tighter
        pattern_xml = re.compile("xml", re.I)
        pattern_js = re.compile("javascript", re.I)
        pattern_json = re.compile("json", re.I)
        pattern_css = re.compile("css", re.I)
        
        # Return the lexer type
        if pattern_xml.search(content):
            return("xml")
        elif pattern_js.search(content):
            return("javascript")
        elif pattern_json.search(content):
            return("javascript")
        elif pattern_css.search(content):
            return("css")
        else:
            return(None)

    ####
    # Decoder tool section
    ####
    
    def encode_data(self):
        """ Encode the specified value """
        
        encode_value = str(self.encodeEdit.toPlainText())
        encode_method = self.encodingMethodCombo.currentText()
        value = encoderlib.encode_values(encode_value, encode_method)
        self.decodeEdit.setPlainText(value)
        
    def encode_wrap(self):
        """ Wrap the specified values in the encode window """
        
        encode_value = str(self.encodeEdit.toPlainText())
        wrap_value = self.encodingWrapCombo.currentText()
        value = encoderlib.wrap_encode(encode_value, wrap_value)
        self.encodeEdit.setPlainText(value)
        
    def decode_data(self):
        """ Decode the specified value from the decoder interface """
        
        decode_value = str(self.decodeEdit.toPlainText())
        decode_method = self.decodeMethodCombo.currentText()
        value = encoderlib.decode_values(decode_value, decode_method)
        self.encodeEdit.setPlainText(value)
        
    def decode_wrap(self):
        """ Wrap the specified values in the decode window """
        
        decode_value = str(self.decodeEdit.toPlainText())
        wrap_value = self.decodeWrapCombo.currentText()
        value = encoderlib.wrap_decode(decode_value, wrap_value)
        self.decodeEdit.setPlainText(value)
                                                             
    def zoom_in(self):
        """ Zoom in on the items in the selected tab """
        self.framework.signal_zoom_in()

    def zoom_out(self):
        """ Zoom out on the items in the selected tab """
        self.framework.signal_zoom_out()

    def sitemap_context_menu(self, point):
        """ Display the context menu for the sitemap """
        self.treeViewSitemapMenu.exec_(self.treeViewSitemap.mapToGlobal(point))

    def sitemap_copy_url(self):
        index = self.treeViewSitemap.currentIndex()
        if index and index.isValid():
            obj = index.internalPointer()
            if obj.url:
                QApplication.clipboard().setText(obj.url)

    def diff(self):
        """ Launch Diff dialog and Diff 2 responses """
        
        myDiffDialog = DiffDialog(self.framework)
        myDiffDialog.show()
        myDiffDialog.exec_()

    def raft_config_toggle(self, configName, status):
        configValue = 'False'
        if status:
            configValue = 'True'
        self.framework.set_raft_config_value(configName, configValue)

    def display_about(self):
        dialog = RaftAboutDialog()
        dialog.show()
        dialog.exec_()
        
    def display_message(self, message):
        dialog = SimpleDialog(message)
        dialog.exec_()

    def display_confirm_dialog(self, message):
        response = QMessageBox.question(self, 'Confirm', message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if 0 != (response & QMessageBox.Yes):
            return True
        else:
            return False
    
    def detach_encoder(self):
        index = self.mainTabWidget.indexOf(self.tabMainEncoder)
        if -1 != index:
            tabText = self.mainTabWidget.tabText(index)
            dialog = QDialog()
            dialog.setWindowTitle(tabText)
            verticalLayout = QVBoxLayout(dialog)
            tabWidget = QTabWidget(dialog)
            verticalLayout.addWidget(tabWidget)
            self.tabMainEncoder.setParent(tabWidget)
            tabWidget.addTab(self.tabMainEncoder, tabText)
            dialog.finished.connect(lambda code: self.reattach_encoder(code, index))
            dialog.show()
            dialog.exec_()

    def reattach_encoder(self, code, index):
        self.tabMainEncoder.setParent(self.mainTabWidget)
        self.mainTabWidget.addTab(self.tabMainEncoder, 'Encoder')
        
    def display_config(self):
        dialog = ConfigDialog(self.framework, self)
        dialog.show()
        dialog.exec_()
        
    def display_analysis_config(self):
        dialog = AnalysisConfigDialog(self.framework, self)
        
        #Instantiate all found analyzers
        self.analyzerlist.instantiate_analyzers(useallanalyzers=True)
        analyzerdict=TreeWidgetTools.obj_list_to_dict(self.analyzerlist,valueattr='isenabled')
        
        TreeWidgetTools.populate_tree_widget(dialog.analyzerList,analyzerdict)
        dialog.analyzerList.setSortingEnabled(True)
        dialog.analyzerList.sortItems(0,0)
        #generated.setParent(dialog.LeftWidget)
        #dialog.verticalLayoutTopLeft.addWidget(generated)
        
        #dialog.analyzerList=generated
        
        dialog.analyzerList.clicked.connect(dialog.viewItemSelected)
        dialog.defaultsButton.clicked.connect(dialog.defaultsButtonClicked)
        dialog.saveAllButton.clicked.connect(dialog.saveAllButtonClicked)
        dialog.closeButton.clicked.connect(dialog.closeButtonClicked)
        dialog.saveButton.clicked.connect(dialog.saveButtonClicked)
        dialog.addnodeButton.clicked.connect(dialog.addnodeButtonClicked)
        dialog.delnodeButton.clicked.connect(dialog.delnodeButtonClicked)
        
        #Setup complete, display dialog
        dialog.show()
        dialog.exec_()
        
    def display_sequence(self):
        dialog = SequenceDialog(self.framework)
        dialog.show()
        dialog.exec_()

    def display_search(self):
        dialog = SearchDialog(self.framework, self)
        dialog.show()
        dialog.exec_()

    def launch_browser(self):
        dialog = RaftBrowserDialog(self.framework, self)
        dialog.show()
        dialog.exec_()
        
    def test(self):
        """ Test Function """
        print("hello world")

class RaftAboutDialog(QDialog, RaftAbout.Ui_aboutDialog):
    """ About dialog for the RAFT Tool """
    
    def __init__(self, parent=None):
        super(RaftAboutDialog, self).__init__(parent)
        self.setupUi(self)
        version_string = __version__
        self.versionLabel.setText(version_string)

def exception_hook(exception_type, exception_value, traceback_obj):
    # TODO: improve this
    print('Unhandled Exception!\n%s' % ('\n'.join(traceback.format_exception(exception_type, exception_value, traceback_obj))))

# TODO: App.Notify support for other errors

def main():
    
    # wondering about the seg fault on Ubuntu Linux?
    # https://bugs.launchpad.net/ubuntu/+source/python-qt4/+bug/561303

    app = QApplication(sys.argv)
    arguments = app.arguments()

    dbfilename = None
    for argument in arguments:
        arg = str(argument)
        if arg.endswith(".raftdb") and os.path.isfile(arg):
            dbfilename = arg

    sys.excepthook = exception_hook

    mainWindow = RaftMain(dbfilename)
    mainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
