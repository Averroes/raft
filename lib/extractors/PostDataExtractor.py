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

from .BaseExtractor import BaseExtractor
from io import StringIO, BytesIO
from urllib import parse as urlparse
import cgi
import sys

class PostDataResults():
    def __init__(self):
        self.name_values = []
        self.name_values_dictionary = {}

    def add_name_value(self, name, value, Type = ''):
        if name not in self.name_values_dictionary:
            self.name_values_dictionary[name] = value
            self.name_values.append((name, value, Type))

class PostDataExtractor(BaseExtractor):

    def __init__(self):
        BaseExtractor.__init__(self)

    def process_request(self, request_headers, request_body, charset = 'utf-8'):

        results = PostDataResults()

        if not request_headers:
            request_headers = b''
        if not request_body:
            request_body = b''
        
        content_type = b'application/x-www-form-urlencoded'
        content_disposition = b''
        for line in request_headers.splitlines():
            if b':' in line:
                name, value = [v.strip() for v in line.split(b':', 1)]
                lname = name.lower()
                if b'content-type' == lname:
                    content_type = value
                elif b'content-disposition' == lname:
                    content_dispostion = value

        ctdict = {}
        n = content_type.find(b';')
        if -1 != n:
            content_type, remainder = content_type[0:n].strip(), content_type[n+1:]
            for item in remainder.split(b';'):
                if b'=' in item:
                    name, value = [v.strip() for v in item.split(b'=', 1)]
                    ctdict[str(name.lower(), 'utf-8', 'ignore')] = value # XXX: could these values be treated as strings?

        if b'application/x-www-form-urlencoded' == content_type:
            request_values = request_body.decode('utf-8', 'ignore')
            qs_values = urlparse.parse_qs(request_values, True, errors='ignore')
            for name, value in qs_values.items():
                results.add_name_value(name, value)
        elif b'text/plain' == content_type:
            # treat text plain as url encoded
            request_values = request_body.decode('utf-8', 'ignore')
            qs_values = urlparse.parse_qs(request_values, True, errors='ignore')
            for name, value in qs_values.items():
                results.add_name_value(name, value)
        elif b'multipart/form-data' == content_type:
            # TODO: use FieldStorage?
            fp = BytesIO(request_body)
            qs_values = cgi.parse_multipart(fp, ctdict)
            for name, value in qs_values.items():
                results.add_name_value(name, value)
        else:
            # TODO: should support more types instead of just name/value pairs
            sys.stderr.write('TODO: unsupport content_type: %s\n' % (content_type))
            return None

        return results


if '__main__' == __name__:

    postDataExtractor = PostDataExtractor()
    results = postDataExtractor.process_request(b'', b'a=1&b=2')

    for name, value, Type in results.name_values:
        print((name, value, Type))
