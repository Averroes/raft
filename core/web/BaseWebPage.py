#
# Base web page implementation
#
# Author: Gregory Fleischer (gfleischer@gmail.com)
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

import PyQt4
from PyQt4 import QtWebKit, QtNetwork
from PyQt4.QtCore import *

class BaseWebPage(QtWebKit.QWebPage):
    def __init__(self, framework, parent = None):
        QtWebKit.QWebPage.__init__(self, parent)
        self.__framework = framework
        self.__framework.subscribe_raft_config_populated(self.__raft_config_populated)
        self.__framework.subscribe_raft_config_updated(self.__raft_config_updated)

    def __raft_config_populated(self):
        self.__set_page_settings()

    def __raft_config_updated(self, name, value):
        name = str(name)
        if name in ('browser_web_storage_enabled', 
                    'browser_plugins_enabled', 
                    'browser_java_enabled', 
                    'browser_auto_load_images'):
            self.__set_page_settings()
            
    def __set_page_settings(self):
        settings = self.settings()
        if self.__framework.get_raft_config_value('browser_web_storage_enabled', bool, True):
            settings.enablePersistentStorage(self.__framework.get_web_db_path())
        settings.setAttribute(
            QtWebKit.QWebSettings.PluginsEnabled, 
            self.__framework.get_raft_config_value('browser_plugins_enabled', bool, True)
            )
        settings.setAttribute(
            QtWebKit.QWebSettings.JavaEnabled, 
            self.__framework.get_raft_config_value('browser_java_enabled', bool, True)
            )
        settings.setAttribute(
            QtWebKit.QWebSettings.AutoLoadImages, 
            self.__framework.get_raft_config_value('browser_auto_load_images', bool, True)
            )

        settings.setAttribute(QtWebKit.QWebSettings.JavascriptEnabled, True)

        self.set_page_settings(settings)
