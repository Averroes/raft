#
# this module implements a common framework interface for RAFT
#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#         Nathan Hamiel
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

import traceback
import os
import sys

from PyQt4.QtCore import (Qt, SIGNAL, QObject, QThread, QMutex, QDir)
from PyQt4.QtGui import QFont
from PyQt4.QtNetwork import QNetworkCookieJar

from core.network.InMemoryCookieJar import InMemoryCookieJar

class Framework(QObject):

    X_RAFT_ID = 'X-RAFT-ID'

    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        self._global_cookie_jar = InMemoryCookieJar(self, self)
        self._db = None
        self._contentExtractor = None
        self._networkAccessManager = None
        self._scopeController = None
        self._scopeConfig = None
        self._requestResponseFactory = None
        self.zoom_size = 0
        self.base_font = QFont()
        # Dictionary for RequestResponse objects loaded into cache
        self.rrd_qlock = QMutex()
        self._request_response_cache = {}
        self.home_dir = str(QDir.toNativeSeparators(QDir.homePath()).toUtf8())
        self.raft_dir = self.create_raft_directory(self.home_dir, '.raft')
        self.user_db_dir = self.create_raft_directory(self.raft_dir, 'db')
        self.user_data_dir = self.create_raft_directory(self.raft_dir, 'data')
        self.user_analyzer_dir = self.create_raft_directory(self.raft_dir, 'analyzers')
        self.user_web_path = self.create_raft_directory(self.raft_dir, 'web')
        self.web_db_path = self.user_web_path
        # TODO: there may be a Qt way to give executable path as well
        self._executable_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        self._data_dir = os.path.join(self._executable_path, 'data')
        self._analyzer_dir = os.path.join(self._executable_path, 'analyzers')
        self._raft_config_cache = {}
        # configuration defaults
        self._default_useragent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-us) AppleWebKit/533.21.1 (KHTML, like Gecko) Version/5.0.5 Safari/533.21.1'
        
    def create_raft_directory(self, basepath, dirname):
        dirtarget = os.path.join(basepath, dirname)
        if not os.path.exists(dirtarget):
            os.mkdir(dirtarget)
        return dirtarget

    def useragent(self):
        if self._db is None:
            return self._default_useragent
        if self.get_raft_config_value('browser_custom_user_agent', bool, False):
            return self.get_raft_config_value('browser_user_agent_value', str, self._default_useragent)
        else:
            return self._default_useragent

    def default_useragent(self):
        return self._default_useragent
        
    def getDB(self):
        if self._db is None:
            raise Exception('database is not initialized')
        return self._db

    def setDB(self, db, dbname):
        if self._db is not None:
            raise Exception('database is already initialized')
        self._db = db
        self._db_uuid = self._db.get_db_uuid()
        self.web_db_path = self.create_raft_directory(self.user_web_path, self._db_uuid)
        self._raft_config_cache = {}
        self._request_response_cache = {}
        self.emit(SIGNAL('raftConfigPopulated()'))
        self.emit(SIGNAL('databaseAttached()'))

    def closeDB(self):
        self.emit(SIGNAL('databaseDetached()'))
        self._db = None

    def subscribe_database_events(self, attach_callback, detach_callback):
        QObject.connect(self, SIGNAL('databaseAttached()'), attach_callback, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('databaseDetached()'), detach_callback, Qt.DirectConnection)
        # if database is already available, invoke attach callback directly
        if self._db is not None:
            attach_callback()

    def get_temp_db_filename(self):
        # default filename is temp.raftdb
        return os.path.join(self.user_db_dir, 'temp.raftdb')

    def get_web_db_path(self):
        return self.web_db_path

    def get_user_home_dir(self):
        return self.home_dir

    def get_analyzer_paths(self):
        return [self._analyzer_dir, self.user_analyzer_dir]

    def get_data_dir(self):
        return self._data_dir

    def getContentExtractor(self):
        return self._contentExtractor

    def setContentExtractor(self, contentExtractor):
        self._contentExtractor = contentExtractor

    def getRequestResponseFactory(self):
        return self._requestResponseFactory

    def setRequestResponseFactory(self, requestResponseFactory):
        self._requestResponseFactory = requestResponseFactory

    def getScopeController(self):
        return self._scopeController

    def setScopeController(self, scopeController):
        self._scopeController = scopeController

    def getSpiderConfig(self):
        return self._spiderConfig

    def setSpiderConfig(self, spiderConfig):
        self._spiderConfig = spiderConfig

    def getNetworkAccessManager(self):
        return self._networkAccessManager

    def setNetworkAccessManager(self, networkAccessManager):
        self._networkAccessManager = networkAccessManager

    def subscribe_response_data_added(self, callback):
        QObject.connect(self, SIGNAL('responseDataAdded()'), callback, Qt.DirectConnection) 

    def signal_response_data_added(self):
        self.emit(SIGNAL('responseDataAdded()'))
        QThread.yieldCurrentThread()

    def subscribe_zoom_in(self, callback):
        QObject.connect(self, SIGNAL('zoomIn()'), callback, Qt.DirectConnection) 

    def get_zoom_size(self):
        return self.zoom_size

    def signal_zoom_in(self):
        self.zoom_size += 1
        self.emit(SIGNAL('zoomIn()'))

    def subscribe_zoom_out(self, callback):
        QObject.connect(self, SIGNAL('zoomOut()'), callback, Qt.DirectConnection) 

    def signal_zoom_out(self):
        self.zoom_size -= 1
        self.emit(SIGNAL('zoomOut()'))

    def get_font(self):
        return self.base_font

    def subscribe_responses_cleared(self, callback):
        QObject.connect(self, SIGNAL('responsesCleared()'), callback, Qt.DirectConnection)

    def signal_responses_cleared(self):
        self.emit(SIGNAL('responsesCleared()'))

    def console_log(self, msg):
        print(msg)

    def debug_log(self, msg):
        print('DEBUG', msg)

    def set_global_cookie_jar(self, cookie_jar):
        self._global_cookie_jar = cookie_jar

    def get_global_cookie_jar(self):
        return self._global_cookie_jar

    def subscribe_raft_config_populated(self, callback):
        QObject.connect(self, SIGNAL('raftConfigPopulated()'), callback, Qt.DirectConnection)
        if self._db is not None:
            callback()

    def subscribe_raft_config_updated(self, callback):
        QObject.connect(self, SIGNAL('raftConfigUpdated(QString, QVariant)'), callback, Qt.DirectConnection)

    def set_raft_config_value(self, name, value):
        if self._raft_config_cache.has_key(name):
            if str(value) == str(self._raft_config_cache[name]):
                return
        cursor = self._db.allocate_thread_cursor()
        self._db.set_config_value(cursor, 'RAFT', name, value)
        cursor.close()
        self._db.release_thread_cursor(cursor)
        self._raft_config_cache[name] = value
        self.emit(SIGNAL('raftConfigUpdated(QString, QVariant)'), name, value)

    def get_raft_config_value(self, name, rtype = str, default_value = None):
        if self._raft_config_cache.has_key(name):
            value = self._raft_config_cache[name]
            if value is not None:
                return rtype(value)
            else:
                return default_value
        cursor = self._db.allocate_thread_cursor()
        value = self._db.get_config_value(cursor, 'RAFT', name, rtype, default_value)
        cursor.close()
        self._db.release_thread_cursor(cursor)
        self._raft_config_cache[name] = value
        return value

    def set_config_value(self, component, name, value):
        if 'RAFT' == component.upper():
            self.set_raft_config_value(name, value)
        else:
            cursor = self._db.allocate_thread_cursor()
            self._db.set_config_value(cursor, component, name, value)
            cursor.close()
            self._db.release_thread_cursor(cursor)

    def get_config_value(self, component, name, rtype = str, default_value = None):
        # TODO: implement config cache
        if 'RAFT' == component.upper():
            return self.get_raft_config_value(name, rtype, default_value)
        else:
            cursor = self._db.allocate_thread_cursor()
            value = self._db.get_config_value(cursor, component, name, rtype, default_value)
            cursor.close()
            self._db.release_thread_cursor(cursor)
            return value
    
    def clear_config_value(self, component, name=None):
        cursor = self._db.allocate_thread_cursor()
        value = self._db.clear_config_value(cursor, component, name)
        cursor.close()
        self._db.release_thread_cursor(cursor)
    
    def get_request_response(self, response_id):
        self.rrd_qlock.lock()
        try:
            if self._request_response_cache.has_key(response_id):
                request_response = self._request_response_cache[response_id]
            else:
                request_response = self._request_response_cache[response_id] = self._requestResponseFactory.fill(response_id)
        finally:
            self.rrd_qlock.unlock()
        return request_response

    def report_exception(self, exc):
        print('EXCEPTION:\n%s' % traceback.format_exc(exc))

    def subscribe_add_differ_response_id(self, callback):
        QObject.connect(self, SIGNAL('differAddResponseId(int)'), callback, Qt.DirectConnection)

    def send_response_id_to_differ(self, Id):
        # TODO: consider accepting cursor
        cursor = self._db.allocate_thread_cursor()
        if self._db.add_differ_item(cursor, int(Id)):
            self.emit(SIGNAL('differAddResponseId(int)'), int(Id))
        cursor.close()
        self._db.release_thread_cursor(cursor)

    def subscribe_populate_requester_response_id(self, callback):
        QObject.connect(self, SIGNAL('requesterPopulateResponseId(int)'), callback, Qt.DirectConnection)
        
    def subscribe_populate_webfuzzer_response_id(self, callback):
        QObject.connect(self, SIGNAL('webfuzzerPopulateResponseId(int)'), callback, Qt.DirectConnection)

    def subscribe_populate_domfuzzer_response_id(self, callback):
        QObject.connect(self, SIGNAL('domfuzzerPopulateResponseId(int)'), callback, Qt.DirectConnection)

    def subscribe_populate_domfuzzer_response_list(self, callback):
        QObject.connect(self, SIGNAL('domfuzzerPopulateResponseList(QStringList)'), callback, Qt.DirectConnection)

    def subscribe_populate_spider_response_id(self, callback):
        QObject.connect(self, SIGNAL('spiderPopulateResponseId(int)'), callback, Qt.DirectConnection)

    def subscribe_populate_spider_response_list(self, callback):
        QObject.connect(self, SIGNAL('spiderPopulateResponseList(QStringList)'), callback, Qt.DirectConnection)

    def send_response_id_to_requester(self, Id):
        self.emit(SIGNAL('requesterPopulateResponseId(int)'), int(Id))
        
    def send_response_id_to_webfuzzer(self, Id):
        self.emit(SIGNAL('webfuzzerPopulateResponseId(int)'), int(Id))

    def send_response_id_to_domfuzzer(self, Id):
        self.emit(SIGNAL('domfuzzerPopulateResponseId(int)'), int(Id))

    def send_response_list_to_domfuzzer(self, id_list):
        self.emit(SIGNAL('domfuzzerPopulateResponseList(QStringList)'), id_list)

    def send_response_id_to_spider(self, Id):
        self.emit(SIGNAL('spiderPopulateResponseId(int)'), int(Id))

    def send_response_list_to_spider(self, id_list):
        self.emit(SIGNAL('spiderPopulateResponseList(QStringList)'), id_list)

    def subscribe_add_sequence_builder_response_id(self, callback):
        QObject.connect(self, SIGNAL('sequenceBuilderAddResponseId(int)'), callback, Qt.DirectConnection)

    def send_response_id_to_sequence_builder(self, Id):
        # TODO: consider accepting cursor
        cursor = self._db.allocate_thread_cursor()
        if self._db.add_sequence_builder_manual_item(cursor, int(Id)):
            self.emit(SIGNAL('sequenceBuilderAddResponseId(int)'), int(Id))
        cursor.close()
        self._db.release_thread_cursor(cursor)
        
    def subscribe_sequences_changed(self, callback):
        QObject.connect(self, SIGNAL('sequencesChanged()'), callback, Qt.DirectConnection)

    def signal_sequences_changed(self):
        self.emit(SIGNAL('sequencesChanged()'))

    def report_implementation_error(self, exc):
        print('IMPLEMENTATION ERROR:\n%s' % traceback.format_exc(exc))

    def log_warning(self, msg):
        print('WARNING', msg)

    def subscribe_populate_tester_csrf(self, callback):
        QObject.connect(self, SIGNAL('testerPopulateCSRFResponseId(int)'), callback, Qt.DirectConnection)

    def send_to_tester_csrf(self, Id):
        self.emit(SIGNAL('testerPopulateCSRFResponseId(int)'), int(Id))

    def subscribe_populate_tester_click_jacking(self, callback):
        QObject.connect(self, SIGNAL('testerPopulateClickJackingResponseId(int)'), callback, Qt.DirectConnection)

    def send_to_tester_click_jacking(self, Id):
        self.emit(SIGNAL('testerPopulateClickJackingResponseId(int)'), int(Id))
