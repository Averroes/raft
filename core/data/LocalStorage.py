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

from PyQt4.QtCore import QUrl
from urllib2 import urlparse
from sqlite3 import dbapi2 as sqlite

import os
import re

class LocalStorage():
    def __init__(self, framework):
        self.framework = framework
        self.re_localstorage_search = re.compile(r'^(https?)_(.+?)_\d+\.localstorage')
        self.localstorage_files = []
        self.localstorage = {}

    def visit_localstorage_files(self, obj, dirname, entries):
        for entry in entries:
            m = self.re_localstorage_search.match(entry)
            if m:
                scheme = m.group(1)
                domain_name = m.group(2)
                filename = os.path.join(dirname, entry)
                self.localstorage_files.append((scheme, domain_name, filename))

    def get_localstorage(self):
        return self.localstorage

    def get_base_path(self):
        return os.path.join(self.framework.get_web_db_path(), 'LocalStorage')

    def read_storage(self):
        base_path = self.get_base_path()
        self.localstorage_files = []
        self.localstorage = {}
        os.path.walk(base_path, self.visit_localstorage_files, None)
        for item in self.localstorage_files:
            scheme, domain_name, filename = item
            domain = urlparse.urlunsplit((scheme, domain_name, '', '', ''))

            if not self.localstorage.has_key(domain):
                self.localstorage[domain] = []

            localstorage_db, cursor = None, None
            try:
                localstorage_db = sqlite.connect(filename)
                cursor = localstorage_db.cursor()
                cursor.execute("""SELECT key, value FROM ItemTable""")
                for row in cursor:
                    name, value = [m or '' for m in row]
                    self.localstorage[domain].append((name, value, filename))
                    
                cursor.close()
                cursor = None
                localstorage_db.close()
                localstorage_db = None
            except Exception, error:
                self.framework.report_exception(error)
            finally:
                if cursor:
                    cursor.close()
                    cursor = None
                if localstorage_db:
                    localstorage_db.close()
                    localstorage_db = None
        
        return self.localstorage

    def delete_storage_entry(self, domain, name):
        base_path = self.get_base_path()
        self.localstorage_files = []
        os.path.walk(base_path, self.visit_localstorage_files, None)
        for item in self.localstorage_files:
            scheme, domain_name, filename = item
            if domain == urlparse.urlunsplit((scheme, domain_name, '', '', '')):
                localstorage_db, cursor = None, None
                try:
                    localstorage_db = sqlite.connect(filename)
                    cursor = localstorage_db.cursor()
                    cursor.execute("""DELETE FROM ItemTable WHERE key=?""", [name])
                    localstorage_db.commit()
                    cursor.close()
                    cursor = None
                    localstorage_db.close()
                    localstorage_db = None
                except Exception, error:
                    self.framework.report_exception(error)
                finally:
                    if cursor:
                        cursor.close()
                        cursor = None
                    if localstorage_db:
                        localstorage_db.close()
                        localstorage_db = None

    def update_storage_entry(self, domain, name, value):
        base_path = self.get_base_path()
        self.localstorage_files = []
        os.path.walk(base_path, self.visit_localstorage_files, None)
        found = False
        for item in self.localstorage_files:
            scheme, domain_name, filename = item
            if domain == urlparse.urlunsplit((scheme, domain_name, '', '', '')):
                found = True
                found_filename = filename
                break

        if found:
            filename = found_filename
        else:
            qurl = QUrl.fromUserInput(domain)
            splitted = urlparse.urlsplit(str(qurl.toEncoded()).encode('ascii', 'ignore'))
            scheme = splitted.scheme or 'http'
            domain_name = splitted.hostname or splitted.path
            filename = os.path.join(self.get_base_path(), '%s_%s_0.localstorage' % (scheme, domain_name))
            
            localstorage_db, cursor = None, None
            try:
                localstorage_db = sqlite.connect(filename)
                cursor = localstorage_db.cursor()
                cursor.execute("""CREATE TABLE IF NOT EXISTS ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value TEXT NOT NULL ON CONFLICT FAIL)""")
                localstorage_db.commit()
                cursor.close()
                cursor = None
                localstorage_db.close()
                localstorage_db = None
            except Exception, error:
                self.framework.report_exception(error)
            finally:
                if cursor:
                    cursor.close()
                    cursor = None
                if localstorage_db:
                    localstorage_db.close()
                    localstorage_db = None

        localstorage_db, cursor = None, None
        try:
            localstorage_db = sqlite.connect(filename)
            cursor = localstorage_db.cursor()
            cursor.execute("""SELECT count(1) FROM ItemTable WHERE key=?""", [name])
            rcount = int(cursor.fetchone()[0])
            if 0 == rcount:
                cursor.execute("""INSERT INTO ItemTable (key, value) VALUES (?,?)""", [name, value])
            else:
                cursor.execute("""UPDATE ItemTable SET value=? WHERE key=?""", [value, name])
            localstorage_db.commit()
            cursor.close()
            cursor = None
            localstorage_db.close()
            localstorage_db = None
        except Exception, error:
            self.framework.report_exception(error)
        finally:
            if cursor:
                cursor.close()
                cursor = None
            if localstorage_db:
                localstorage_db.close()
                localstorage_db = None

