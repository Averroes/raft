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

class ScopeController(QObject):
    def __init__(self, framework, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework

        self.re_UrlPathsIncludes = []
        self.re_UrlPathsExcludes = []
        self.re_HostnamesIncludes = []
        self.re_HostnamesExcludes = []
        self.re_IPAddressesIncludes = []
        self.re_IPAddressesExcludes = []

        self.framework.subscribe_database_events(self.db_attach, self.db_detach)
        self.framework.subscribe_raft_config_updated(self.configuration_updated)

    def db_attach(self):
        self.fill_scoping_configuration(self.framework.get_raft_config_value('SCOPING', str))

    def db_detach(self):
        pass

    def configuration_updated(self, name, value):
        if str(name) == 'SCOPING':
            self.fill_scoping_configuration(str(value.toString()))

    def fill_scoping_configuration(self, configuration):
        if configuration:
            obj = json.loads(configuration)
            self.re_UrlPathsIncludes = self.build_url_patterns(obj.get('UrlPathsInclude') or '')
            self.re_UrlPathsExcludes = self.build_url_patterns(obj.get('UrlPathsExclude') or '')
            self.re_HostnamesIncludes = self.build_hostname_patterns(obj.get('HostnamesInclude') or '')
            self.re_HostnamesExcludes = self.build_hostname_patterns(obj.get('HostnamesExclude') or '')
            self.re_IPAddressesIncludes = self.build_ipaddress_patterns(obj.get('IPAddressesInclude') or '')
            self.re_IPAddressesExcludes = self.build_ipaddress_patterns(obj.get('IPAddressesExclude') or '')

    def build_basic_patterns(self, valuelist):
        pattern_list = []
        for line in valuelist.splitlines():
            if not line:
                pass
            if line.startswith('^') or line.endswith('$') or '.*' in line or '.+' in line:
                try:
                    r = re.compile(line)
                    pattern_list.append(r)
                except re.error:
                    pattern_list.append(re.compile(re.escape(line)))
            else:
                pattern_list.append(re.compile(re.escape(line)))
        return pattern_list

    def build_url_patterns(self, valuelist):
        return self.build_basic_patterns(valuelist)

    def build_hostname_patterns(self, valuelist):
        return self.build_basic_patterns(valuelist)

    def build_ipaddress_patterns(self, valuelist):
        return self.build_basic_patterns(valuelist)
            
    def isUrlInScope(self, url, referer):
        inscope = self.apply_scoping_rules(url, referer)
#        print('scoping calculation [%s]->[%s]' % (url, inscope))
        return inscope

    def apply_scoping_rules(self, url, referer):
        splitted = urlparse.urlsplit(url)
        matched_exclusion = False
        matched_inclusion = False
        matched_path_inclusion = False
        matched_url_inclusion = False
        matched_path_exclusion = False
        matched_url_exclusion = False
        any_inclusions = False
        hostname = splitted.hostname
        path = splitted.path or '/'
        for pattern in self.re_UrlPathsIncludes:
            any_inclusions = True
            if pattern.match(path):
                matched_inclusion = True
                matched_path_inclusion = True
                break
            if pattern.match(url):
                matched_inclusion = True
                matched_url_inclusion = True
                break
        for pattern in self.re_UrlPathsExcludes:
            if pattern.match(path):
                matched_exclusion = True
                break
            if pattern.match(url):
                matched_exclusion = True
                break
        if hostname:
            for pattern in self.re_HostnamesIncludes:
                any_inclusions = True
                if pattern.match(hostname):
                    matched_inclusion = True
                    break
            for pattern in self.re_HostnamesExcludes:
                if pattern.match(hostname):
                    matched_exclusion = True
                    break

        if matched_exclusion and not matched_inclusion:
            return False
        elif matched_exclusion and matched_inclusion:
            if matched_url_exclusion and not matched_url_inclusion:
                return False
            elif matched_path_exclusion and not matched_path_inclusion:
                return False
            elif matched_url_inclusion or matched_path_inclusion:
                return True
            else:
                return False

        if matched_inclusion:
            return True
        elif any_inclusions:
            return False
        else:
            if referer:
                splitted2 = urlparse.urlsplit(str(referer))
                if splitted2.hostname != splitted.hostname:
                    return False
            return True
