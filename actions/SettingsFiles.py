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

from xml.sax.saxutils import escape
from lxml import etree

from core.database.constants import ConfigurationTable

def process_export(framework, filename):
    fhandle = None
    cursor = None
    try:
        fhandle = open(filename, 'w')
        fhandle.write('<raftsettings>\n')
        Data = framework.getDB()
        cursor = Data.allocate_thread_cursor()
        for row in Data.read_all_config_values(cursor):
            items = [m or '' for m in row]
            component = str(items[ConfigurationTable.COMPONENT])
            config_name = str(items[ConfigurationTable.CONFIG_NAME])
            config_value = str(items[ConfigurationTable.CONFIG_VALUE])
            fhandle.write('<raftsetting>\n')
            fhandle.write('<component>%s</component>\n' % escape(component))
            fhandle.write('<config_name>%s</config_name>\n' % escape(config_name))
            fhandle.write('<config_value>%s</config_value>\n' % escape(config_value))
            fhandle.write('</raftsetting>\n')
        fhandle.write('</raftsettings>\n')
    finally:
        if cursor:
            Data.release_thread_cursor(cursor)
        if fhandle:
            fhandle.close()

def process_import(framework, filename):
    fhandle = None
    try:
        fhandle = open(filename, 'r')
        dom = etree.parse(fhandle)
        for settings in dom.getroot().findall('raftsetting'):
            component = str(settings.find('component').text)
            config_name = str(settings.find('config_name').text)
            config_value = str(settings.find('config_value').text)
            if 'RAFT' == component:
                framework.set_raft_config_value(config_name, config_value)
            else:
                framework.set_config_value(component, config_name, config_value)
    finally:
        if fhandle:
            fhandle.close()
            fhandle = None
