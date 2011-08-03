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

from urllib2 import urlparse
import re

class BaseExtractor():
    def __init__(self):
        self.host_spec = r'(?:https?:)?//(?:[-a-zA-Z0-9_]+\.)+[a-zA-Z]{2,}'
        self.path_spec = r'[-a-zA-Z0-9%$_.!*\'(),/=:]+(?:\?[^#]*)?'
        self.relative_spec = r'(?:^|\b)(?:\.\.[/]|\.[/]|[^:</][/])%s' % (self.path_spec)

        self.re_full_url = re.compile('%s/(?:%s)?' % (self.host_spec, self.path_spec))
        self.re_relative_url = re.compile(self.relative_spec)

    def getBaseType(self, content_type):
        # TODO: improve
        if 'html' in content_type:
            return 'html'
        return content_type

    def getExtractor(self, content_type):
        import HtmlExtractor
        import PostDataExtractor
        base_type = self.getBaseType(content_type)
        if 'html' == content_type:
            return HtmlExtractor.HtmlExtractor()
        elif 'post-data' == content_type:
            return PostDataExtractor.PostDataExtractor()
#        elif 'javascript' == content_type:
#            return JSExtractor()
        else:
            raise Exception('Unknown extractor: %s' % content_type)

    def parseContentType(self, contentType):
        # TODO implement better detection based on content-type
        charset = ''
        if contentType:
            if ';' in contentType:
                contentType, remainder = [v.strip() for v in contentType.split(';', 1)]
                if remainder:
                    lookup = 'charset='
                    n = remainder.lower().find(lookup)
                    if n > -1:
                        charset = remainder[n+len(lookup):].strip()

        if not charset:
            charset = 'utf-8'

        return contentType, charset
