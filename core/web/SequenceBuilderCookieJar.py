#
# Cookie jar for sequence building
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

from core.network.InMemoryCookieJar import InMemoryCookieJar
from urllib import parse as urlparse

class SequenceBuilderCookieJar(InMemoryCookieJar):
    def __init__(self, framework, parent = None):
        InMemoryCookieJar.__init__(self, framework, parent)
        self.framework = framework
        self.cookie_tracking = False
        self.cookie_items = {}
        self.tracked_cookies = []

    def start_tracking(self):
        self.cookie_tracking = True

    def stop_tracking(self):
        self.cookie_tracking = False

    def clear_cookies(self):
        self.cookie_items.clear()
        InMemoryCookieJar.clear_cookies(self)

    def setCookiesFromUrl(self, cookieList, url):
        if self.cookie_tracking:
            for cookie in cookieList:
                cookie_domain = str(cookie.domain())
                if not cookie_domain:
                    cookie_domain = str(url.encodedHost())
                if cookie_domain not in self.cookie_items:
                    self.cookie_items[cookie_domain] = {}
                self.cookie_items[cookie_domain][str(cookie.name())] = str(cookie.value())

        return InMemoryCookieJar.setCookiesFromUrl(self, cookieList, url)
    
    def is_cookie_tracked(self, cookie_domain, cookie_name):
        if cookie_domain in self.cookie_items:
            if cookie_name in self.cookie_items[cookie_domain]:
                return True
        elif cookie_domain.startswith('.'):
            cookie_domain = cookie_domain[1:]
            if cookie_domain in self.cookie_items and cookie_name in self.cookie_items[cookie_domain]:
                return True

        print(('OOPS', cookie_domain, list(self.cookie_items.keys())))
        
        return False
        
