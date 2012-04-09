#
# extract name/value pairs from post request data
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
from cStringIO import StringIO
from urllib2 import urlparse
import cgi
import sys

class PostDataResults():
    def __init__(self):
        self.name_values = []
        self.name_values_dictionary = {}

    def add_name_value(self, name, value, Type = ''):
        if not self.name_values_dictionary.has_key(name):
            self.name_values_dictionary[name] = value
            self.name_values.append((name, value, Type))

class PostDataExtractor(BaseExtractor):

    def __init__(self):
        BaseExtractor.__init__(self)

    def process_request(self, request_headers, request_body, charset = 'utf-8'):

        results = PostDataResults()

        if not request_headers:
            request_headers = ''
        if not request_body:
            request_body = ''
        
        content_type = 'application/x-www-form-urlencoded'
        content_disposition = ''
        for line in request_headers.splitlines():
            if ':' in line:
                name, value = [v.strip() for v in line.split(':', 1)]
                lname = name.lower()
                if 'content-type' == lname:
                    content_type = value
                elif 'content-disposition' == lname:
                    content_dispostion = value

        ctdict = {}
        n = content_type.find(';')
        if -1 != n:
            content_type, remainder = content_type[0:n].strip(), content_type[n+1:]
            for item in remainder.split(';'):
                if '=' in item:
                    name, value = [v.strip() for v in item.split('=', 1)]
                    ctdict[name.lower()] = value

        if 'application/x-www-form-urlencoded' == content_type:
            qs_values = urlparse.parse_qs(request_body, True)
            for name, value in qs_values.iteritems():
                results.add_name_value(name, value)
        elif 'text/plain' == content_type:
            # treat text plain as url encoded
            qs_values = urlparse.parse_qs(request_body, True)
            for name, value in qs_values.iteritems():
                results.add_name_value(name, value)
        elif 'multipart/form-data' == content_type:
            fp = StringIO(request_body)
            qs_values = cgi.parse_multipart(fp, ctdict)
            for name, value in qs_values.iteritems():
                results.add_name_value(name, value)
        else:
            # TODO: should support more types instead of just name/value pairs
            sys.stderr.write('TODO: unsupport content_type: %s\n' % (content_type))
            return None

        return results


if '__main__' == __name__:

    postDataExtractor = PostDataExtractor()
    results = postDataExtractor.process_request('', 'a=1&b=2')

    for name, value, Type in results.name_values:
        print(name, value, Type)
