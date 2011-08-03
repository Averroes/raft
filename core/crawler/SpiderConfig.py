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

from PyQt4.QtCore import Qt, QObject, SIGNAL, QUrl
import json
import re
from urllib2 import urlparse

class SpiderConfig(QObject):
    def __init__(self, framework, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework

        self.re_dangerous_path = None

        self.framework.subscribe_raft_config_populated(self.configuration_populated)
        self.framework.subscribe_raft_config_updated(self.configuration_updated)

    def configuration_populated(self):
        self.fill_spider_configuration(self.framework.get_raft_config_value('SPIDER', str))

    def configuration_updated(self, name, value):
        if str(name) == 'SPIDER':
            self.fill_spider_configuration(str(value.toString()))

    def fill_spider_configuration(self, configuration):
        if configuration:
            obj = json.loads(configuration)
        else:
            obj = {}
        self.submit_forms = bool(obj.get('submit_forms') or True)
        self.use_data_bank = bool(obj.get('use_data_bank') or True)
        self.submit_user_name_password = bool(obj.get('submit_user_name_password') or True)
        self.evaluate_javascript = bool(obj.get('evaluate_javascript') or True)
        self.iterate_user_agents = bool(obj.get('iterate_user_agents') or True)
        self.retrieve_media_files = bool(obj.get('retrieve_media_files') or True)
        self.exclude_dangerous_paths = bool(obj.get('exclude_dangerous_paths') or False)
        self.dangerous_path = str(obj.get('dangerous_path') or 'delete|remove|destroy')
        self.max_links = int(obj.get('max_links') or 8192)
        self.max_link_depth = int(obj.get('max_link_depth') or 5)
        self.max_children = int(obj.get('max_children') or 256)
        self.max_unique_parameters = int(obj.get('max_unique_parameters') or 16)
        self.redundant_content_limit = int(obj.get('redundant_content_limit') or 128)
        self.redundant_structure_limit = int(obj.get('redundant_structure_limit') or 256)
        self.media_extensions = str(obj.get('media_extensions') or 'wmv,mp3,mp4,mpa,gif,jpg,jpeg,png')
        
        if self.exclude_dangerous_paths:
            try:
                self.re_dangerous_path = re.compile(self.dangerous_path)
            except re.error, error:
                self.log_warning('Failed to compile RE [%s]: %s' (self.dangerous_path, error))
            # TODO: or should this fail completely?
            self.exclude_dangerous_paths = False

