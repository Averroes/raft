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

from BaseExtractor import BaseExtractor
from JSParser import JSParser
from urllib2 import urlparse
import re

class JSParseResults():
    def __init__(self, baseurl, encoding):
        self.baseurl = baseurl
        self.encoding = encoding
        self.comments = []
        self.strings = []
        self.relative_links = []
        self.links = []

    def resolve_url(self, uri):
        splitted = urlparse.urlsplit(uri)
        if not splitted.scheme and splitted.path and not splitted.path.startswith('/'):
            if splitted.path not in self.relative_links:
                self.relative_links.append(splitted.path)
        # TODO: urljoin doesn't understand example.com/foo relative links
        resolved = urlparse.urljoin(self.baseurl, uri)
        return resolved

    def add_strings(self, strings):
        for string in strings:
            if not string in self.strings:
                self.strings.append(string)

    def add_comments(self, comments):
        for comment in comments:
            if not comment in self.comments:
                self.comments.append(comment)

    def add_relative_uri(self, uri):
        if uri not in self.relative_links:
            self.relative_links.append(uri)

    def add_uri(self, uri):
        resolved = self.resolve_url(uri)
        if resolved not in self.links:
            self.links.append(resolved)


class JSExtractor(BaseExtractor):
    def __init__(self):
        BaseExtractor.__init__(self)
        self.jsParser = JSParser()

    def process(self, script, baseurl, encoding = 'utf-8', results = None):

        if results is None:
            results = JSParseResults(script, baseurl)

        self.jsParser.parse(script, '', 0)
        comments = self.jsParser.comments()
        strings = self.jsParser.strings()
        results.add_comments(comments)
        results.add_strings(strings)

        for string in strings:
            for line in string.splitlines():
                match = self.re_full_url.search(line)
                if match:
                    results.add_uri(match.group(0))
                match = self.re_relative_url.search(line)
                if match:
                    results.add_relative_uri(match.group(0))

        for comment in comments:
            print(comment)
            for line in comment.splitlines():
                match = self.re_full_url.search(line)
                if match:
                    results.add_uri(match.group(0))
                match = self.re_relative_url.search(line)
                if match:
                    results.add_relative_uri(match.group(0))

        return results
        
if '__main__' == __name__:

    import sys
    filename = sys.argv[1]
    url = sys.argv[2]
    contents = open(filename).read()
    
    extractor = JSExtractor()
    results = extractor.process(contents, url)

    for link in results.links:
        print('link: %s' % link)

    for link in results.relative_links:
        print('relative link: %s' % link)

