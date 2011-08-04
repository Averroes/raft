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

from pyamf import sol
import os
import platform

class FlashCookies:
    def __init__(self, framework):
        self.framework = framework
        self.detect_platform()

    def detect_platform(self):
        self.is_mac = False
        self.is_windows = False
        self.is_linux = False
        if 'Darwin' == platform.system():
            self.is_mac = True
        elif 'Windows' == platform.system():
            self.is_windows = True
        else:
            # assume mac
            self.is_mac = True

    def visit_flashcookies_files(self, obj, dirname, entries):
        for entry in entries:
            if not obj.has_key('randomized'):
                if entry not in ('.','..'):
                    obj['randomized'] = entry
            if entry.endswith('.sol'):
                self.flashcookies_files.append((dirname, entry))

    def get_base_path(self):
        if self.is_mac:
            base_path = os.path.join(self.framework.get_user_home_dir(), 'Library/Preferences/Macromedia/Flash Player/#SharedObjects/')
        elif self.is_windows:
            base_path = os.path.join(self.framework.get_user_home_dir(), 'Application Data\\Macromedia\\Flash Player\\#SharedObjects\\')
        else:
            # assume linux or similar
            base_path = os.path.join(self.framework_get_user_home_dir(), '.macromedia/Flash_Player/#SharedObjects/')

        return base_path

    def read_flashcookies(self):
        base_path = self.get_base_path()
        self.flashcookies_files = []
        self.flashcookies = {}
        user_dir = {}
        os.path.walk(base_path, self.visit_flashcookies_files, user_dir)
        for item in self.flashcookies_files:
            try:
                dirname, entry = item
                filename = os.path.join(dirname, entry)
                n = dirname.find(user_dir['randomized'])
                if n > -1:
                    domain = dirname[n+len(user_dir['randomized'])+1:]
                    n = domain.find(os.path.sep)
                    if n > -1:
                        domain = domain[:n]
                    if not self.flashcookies.has_key(domain):
                        self.flashcookies[domain] = []
                    lso = sol.load(filename)
                    self.flashcookies[domain].append(lso)
            except Exception, error:
                self.framework.report_exception(error)
        
        return self.flashcookies
            


