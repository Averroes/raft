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
from urllib import parse as urlparse

class SpiderConfig(QObject):
    def __init__(self, framework, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework

        self.re_dangerous_path = None
        self.re_media_extension = None

        self.default_dangerous_paths = 'delete|remove|destroy'
        self.default_media_extensions = 'wmv,mp3,mp4,mpa,gif,jpg,jpeg,png'

        self.framework.subscribe_raft_config_populated(self.configuration_populated)
        self.framework.subscribe_raft_config_updated(self.configuration_updated)

    def configuration_populated(self):
        self.fill_spider_configuration(self.framework.get_raft_config_value('SPIDER', str))

    def configuration_updated(self, name, value):
        if name == 'SPIDER':
            self.fill_spider_configuration(value)

    def config_value_or_default(self, obj, config_name, default_value):
        if config_name in obj:
            return obj[config_name]
        elif default_value is not None:
            return default_value
        else:
            return ''

    def fill_spider_configuration(self, configuration):
        if configuration:
            obj = json.loads(configuration)
        else:
            obj = {}
        self.submit_forms = bool(self.config_value_or_default(obj, 'submit_forms', True))
        self.use_data_bank = bool(self.config_value_or_default(obj, 'use_data_bank', True))
        self.submit_user_name_password = bool(self.config_value_or_default(obj, 'submit_user_name_password', True))
        self.evaluate_javascript = bool(self.config_value_or_default(obj, 'evaluate_javascript', True))
        self.iterate_user_agents = bool(self.config_value_or_default(obj, 'iterate_user_agents', True))
        self.retrieve_media_files = bool(self.config_value_or_default(obj, 'retrieve_media_files', True))
        self.exclude_dangerous_paths = bool(self.config_value_or_default(obj, 'exclude_dangerous_paths', False))
        self.dangerous_path = str(self.config_value_or_default(obj, 'dangerous_path', self.default_dangerous_paths))
        self.max_links = int(self.config_value_or_default(obj, 'max_links', 8192))
        self.max_link_depth = int(self.config_value_or_default(obj, 'max_link_depth', 6))
        self.max_children = int(self.config_value_or_default(obj, 'max_children', 256))
        self.max_unique_parameters = int(self.config_value_or_default(obj, 'max_unique_parameters', 16))
        self.redundant_content_limit = int(self.config_value_or_default(obj, 'redundant_content_limit', 128))
        self.redundant_structure_limit = int(self.config_value_or_default(obj, 'redundant_structure_limit', 256))
        self.media_extensions = str(self.config_value_or_default(obj, 'media_extensions', self.default_media_extensions))
        
        if self.exclude_dangerous_paths:
            try:
                self.re_dangerous_path = re.compile(self.dangerous_path, re.I)
            except re.error as error:
                self.log_warning('Failed to compile RE [%s]: %s' (self.dangerous_path, error))
                # TODO: or should this fail completely?
                self.re_dangerous_path = re.compile(self.default_dangerous_paths, re.I)

        if not self.retrieve_media_files:
            try:
                self.re_media_extensions = self.make_media_extension_re(self.media_extensions)
            except re.error as error:
                self.re_media_extensions = self.make_media_extension_re(self.default_media_extensions)
    
    def make_media_extension_re(self, extension_string):
        if extension_string is None or '' == extension_string:
            extension_string = self.default_media_extensions
        extensions = []
        for extension in self.media_extensions.split(','):
            if extension.startswith('\\.'):
                extensions.append(extension)
                pass
            elif extension.startswith('.'):
                extensions.append(re.escape(extension))
            else:
                extensions.append('\.'+re.escape(extension))
            return re.compile('^(?:%s)$' % '|'.join(extensions))
        
