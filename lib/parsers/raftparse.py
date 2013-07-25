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
from lxml import etree
import sys
import bz2
import gzip
import lzma
import re
from urllib import parse as urlparse
import logging, traceback
from io import StringIO
from xml.sax.saxutils import escape
import base64

class ParseAdapter:
    re_nonprintable = re.compile(bytes('[^%s]' % re.escape('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r'),'ascii'))
    re_nonprintable_str = re.compile('[^%s]' % re.escape('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r'))
    re_apply_escape_str = re.compile('[^%s]' % re.escape('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%()*+,-./:;=?@[\\]^_`{|}~ \t\n\r'))
    def __init__(self):
        pass

    def adapt(self, result):
        return ParseAdapter.Capture(result)

    def write_xml(self, results, fmt, value, func = str):
        if value is None:
            return
        try:
            value = func(value)
            if str == type(value):
                pass
            elif bytes == type(value):
                value = value.decode('utf-8', 'ignore')
            else:
                value = str(value)
            if self.re_nonprintable_str.search(value):
                results.write(fmt % re_apply_escape_str.sub(lambda m: '&#x%02X;' % (ord(m.group(0))), value))
            else:
                results.write(fmt % escape(value))
        except ValueError:
            pass

    def write_encoded_xml(self, results, tagname, value):
        is_str = type(value) == str
        if is_str:
            bvalue = value.encode('utf-8')
        else:
            bvalue = value

        if self.re_nonprintable.search(bvalue):
            results.write('<%s encoding="base64">' % tagname)
            results.write(base64.b64encode(bvalue).decode('ascii'))
            results.write('</%s>\n' % tagname)
        else:
            results.write('<%s>' % tagname)
            if is_str:
                results.write(escape(value))
            else:
                results.write(escape(value.decode('ascii')))
            results.write('</%s>\n' % tagname)

    def format_as_xml(self, capture):
        results = StringIO()
        results.write('<capture>\n')
        results.write('<request>\n')
        self.write_xml(results, '<method>%s</method>\n', capture.method)
        self.write_encoded_xml(results, 'url', capture.url)
        self.write_xml(results, '<host>%s</host>\n', capture.host)
        self.write_xml(results, '<hostip>%s</hostip>\n', capture.hostip)
        self.write_xml(results, '<datetime>%s</datetime>\n', capture.datetime)
        self.write_encoded_xml(results, 'headers', capture.request_headers)
        self.write_encoded_xml(results, 'body', capture.request_body)
        results.write('</request>\n')
        results.write('<response>\n')
        self.write_xml(results, '<status>%s</status>\n', capture.status)
        self.write_xml(results, '<content_type>%s</content_type>\n', capture.content_type)
        self.write_xml(results, '<content_length>%s</content_length>\n', capture.content_length, int)
        self.write_xml(results, '<elapsed>%s</elapsed>\n', capture.elapsed, int)
        self.write_encoded_xml(results, 'headers', capture.response_headers)
        self.write_encoded_xml(results, 'body', capture.response_body)
        results.write('</response>\n')

        if capture.notes is not None or capture.confirmed is not None:
            results.write('<analysis>\n')
            self.write_xml(results, '<notes>%s</notes>\n', capture.notes)
            self.write_xml(results, '<confirmed>%s</confirmed>\n', capture.confirmed)
            results.write('</analysis>\n')

        results.write('</capture>\n')

        return results.getvalue()

    class Capture:
        def __init__(self, result):
            self.origin, self.host, self.hostip, self.url, self.status, self.datetime, request, response, self.method, self.content_type, extras = result
            if request:
                self.request_headers = request[0]
                self.request_body = request[1]
            else:
                self.request_headers = b''
                self.request_body = b''
            if response:
                self.response_headers = response[0]
                self.response_body = response[1]
            else:
                self.response_headers = b''
                self.response_body = b''

            self.extras = extras
            if extras and isinstance(extras, dict):
                self.content_length = extras.get('content_length')
                self.elapsed = extras.get('elapsed')
                self.notes = extras.get('notes')
                self.confirmed = extras.get('confirmed')
            else:
                self.content_length = ''
                self.elapsed = ''
                self.notes = ''
                self.confirmed = ''

class raft_parse_xml():
    """ Parses Raft XML file into request and result data """

    S_INITIAL = 1
    S_RAFT = 2
    S_CAPTURE = 3
    S_REQUEST = 4
    S_RESPONSE = 5
    S_ANALYSIS = 6
    S_HEADERS = 7
    S_BODY = 8
    S_COOKIES = 9
    S_COOKIE = 10
    S_REQUEST_XML_ELEMENT = 101
    S_RESPONSE_XML_ELEMENT = 102
    S_ANALYSIS_XML_ELEMENT = 103
    S_COOKIE_XML_ELEMENT = 104

    I_HEADERS = 0
    I_BODY = 1
    I_HEADERS_ENCODING = 2
    I_BODY_ENCODING = 3

    re_request_line = re.compile(br'^(OPTIONS|GET|HEAD|POST|PUT|DELETE|TRACE|CONNECT|\w+)\s+((?:http|/).+?)(?:\s+(HTTP/\d\.\d))?$')
    re_status_line = re.compile(br'^(HTTP/\d\.\d)\s+(\d{3})(?:\s+(.*))?$')

    def __init__(self, raftfile):
        if raftfile.lower().endswith('.xml.bz2'):
            self.source = bz2.BZ2File(raftfile, 'rb')
        elif raftfile.lower().endswith('.xml.gz'):
            self.source = gzip.GzipFile(raftfile, 'rb')
        elif raftfile.lower().endswith('.xml.xz'):
            self.source = lzma.LZMAFile(raftfile, 'rb')
        elif raftfile.lower().endswith('.xml'):
            self.source = open(raftfile, 'rb')
        else:
            raise Exception('Unsupported file type for %s' % (raftfile))

        self.raftfile = raftfile

        # http://effbot.org/zone/element-iterparse.htm#incremental-parsing
        self.context = etree.iterparse(self.source, events=('start', 'end'), huge_tree = True)
        self.iterator = iter(self.context)
        self.root = None

        self.version = 1
        self.states = [self.S_INITIAL]
        self.state_table = {
            self.S_INITIAL : (
                ('start', 'raft', self.raft_start),
                ),
            self.S_RAFT : (
                ('start', 'capture', self.capture_start),
                ('start', 'cookies', self.cookies_start),
                ('end', 'raft', self.raft_end),
                ),
            self.S_CAPTURE : (
                ('start', 'request', self.request_start),
                ('start', 'response', self.response_start),
                ('start', 'analysis', self.analysis_start),
                ('end', 'capture', self.capture_end),
                ),
            self.S_REQUEST : (
                ('start', 'method', self.request_xml_element_start),
                ('start', 'url', self.request_xml_element_start),
                ('start', 'host', self.request_xml_element_start),
                ('start', 'hostip', self.request_xml_element_start),
                ('start', 'datetime', self.request_xml_element_start),
                ('start', 'headers', self.headers_start),
                ('start', 'body', self.body_start),
                ('end', 'request', self.request_end),
                ),
            self.S_RESPONSE : (
                ('start', 'status', self.response_xml_element_start),
                ('start', 'content_type', self.response_xml_element_start),
                ('start', 'content_length', self.response_xml_element_start),
                ('start', 'elapsed', self.response_xml_element_start),
                ('start', 'headers', self.headers_start),
                ('start', 'body', self.body_start),
                ('end', 'response', self.response_end),
                ),
            self.S_ANALYSIS : (
                ('start', 'notes', self.analysis_xml_element_start),
                ('start', 'confirmed', self.analysis_xml_element_start),
                ('end', 'analysis', self.analysis_end),
                ),
            self.S_HEADERS : (
                ('end', 'headers', self.headers_end),
                ),
            self.S_BODY : (
                ('end', 'body', self.body_end),
                ),
            self.S_REQUEST_XML_ELEMENT : (
                ('end', 'method', self.xml_element_end),
                ('end', 'url', self.xml_encoded_element_end),
                ('end', 'host', self.xml_element_end),
                ('end', 'hostip', self.xml_element_end),
                ('end', 'datetime', self.xml_element_end),
                ),
            self.S_RESPONSE_XML_ELEMENT : (
                ('end', 'status', self.xml_element_end),
                ('end', 'content_type', self.xml_element_end),
                ('end', 'content_length', self.xml_element_end),
                ('end', 'elapsed', self.xml_element_end),
                ),
            self.S_ANALYSIS_XML_ELEMENT : (
                ('end', 'notes', self.xml_element_end),
                ('end', 'confirmed', self.xml_element_end),
                ),
            self.S_COOKIES : (
                ('start', 'cookie', self.cookie_start),
                ('end', 'cookies', self.cookies_end),
                ),
            self.S_COOKIE : (
                ('start', 'raw', self.cookie_xml_element_start),
                ('end', 'cookie', self.cookie_end),
                ),
            self.S_COOKIE_XML_ELEMENT : (
                ('end', 'raw', self.cookie_xml_element_end),
                ),
            }
        self.default_capture_values = (
                ('method', ''),
                ('url', ''),
                ('host', ''),
                ('hostip', ''),
                ('datetime', ''),
                ('status', ''),
                ('content_type', ''),
                ('content_length', ''),
                ('elapsed', ''),
                ('notes', ''),
                ('confirmed', ''),
            )

    def populate_missing(self, host, status, url, datetime, method, content_type, request, response):

        # handle request
        if not host or not url or not method:
            if request and request[0]:
                request_headers = request[0]
                request_url = b''
                for line in request_headers.splitlines():
                    line = line.rstrip()
                    m = self.re_request_line.search(line)
                    if m:
                        if not method:
                            method = (m.group(1) or b'').decode('ascii', 'ignore')
                        request_url = m.group(2)
                    elif b':' in line:
                        name, value = line.split(b':', 1)
                        lname = name.lower()
                        if not host and b'host' == lname:
                            host = value.strip().decode('utf-8', 'ignore')
                if not url:
                    splitted = urlparse.urlsplit(request_url)
                    if not host:
                        host = (splitted.hostname or b'').decode('utf-8', 'ignore')
                    scheme = (splitted.scheme or b'').decode('utf-8', 'ignore') or 'http'
                    url = urlparse.urlunsplit((scheme, host, (splitted.path or b'').decode('utf-8', 'ignore'), (splitted.query or b'').decode('utf-8', 'ignore'), ''))

        if False:
            # TODO: some broken servers send the response headers in the request body :(
            # should this "automagically" find the correct values?
            indices = (0,1)
        else:
            indices = (0,)

        for index in indices:
            # TODO: handle 100 Continue
            if not status or not datetime or not content_type:
                if response and response[index]:
                    response_headers = response[index]
                    for line in response_headers.splitlines():
                        line = line.rstrip()
                        if not line:
                            break
                        m = self.re_status_line.search(line)
                        if m:
                            if not status:
                                status = (m.group(2) or b'').decode('utf-8', 'ignore')
                        elif b':' in line:
                            name, value = line.split(b':', 1)
                            lname = name.lower()
                            if not datetime and b'date' == lname:
                                datetime = value.strip().decode('utf-8', 'ignore')
                            elif not content_type and b'content-type' == lname:
                                content_type = value.strip().decode('utf-8', 'ignore')
            if status and datetime and content_type:
                break

        return (host, status, url, datetime, method, content_type)

    def make_results(self):
        cur = self.current

        host = cur['host']
        hostip = cur['hostip']
        status = ''
        try:
            status = int(cur['status'])
        except ValueError:
            pass
        except TypeError:
            pass
        url = cur['url']
        datetime = cur['datetime']
        method = cur['method']
        content_type = cur['content_type']

        request = cur['request']
        response = cur['response']

        # populate missing values based on request/response content
        if not host or not status or not url or not datetime or not method or not content_type:
            host, status, url, datetime, method, content_type = self.populate_missing(host, status, url, datetime, method, content_type, request, response)

        return ('CAPTURE', host, hostip, url, status, datetime, request, response, method, content_type, {'content_length':cur['content_length'], 'elapsed':cur['elapsed'], 'notes':cur['notes'], 'confirmed':cur['confirmed']})

    def raft_start(self, elem):
        self.root = elem
        self.states.append(self.S_RAFT)

    def raft_end(self, elem):
        raise(StopIteration)

    def capture_start(self, elem):
        self.current = {
            'request' : ['','','none','none'],
            'response' : ['','','none','none'],
            }
        for n, v in self.default_capture_values:
            self.current[n] = v

        self.current_hb = None
        self.states.append(self.S_CAPTURE)

    def capture_end(self, elem):
        elem.clear()
        self.root.clear()
        self.states.pop()
        return self.make_results()

    def request_start(self, elem):
        self.current_hb = self.current['request']
        self.states.append(self.S_REQUEST)

    def request_end(self, elem):
        self.current_hb = None
        self.states.pop()

    def response_start(self, elem):
        self.current_hb = self.current['response']
        self.states.append(self.S_RESPONSE)

    def response_end(self, elem):
        self.current_hb = None
        self.states.pop()

    def headers_start(self, elem):
        if 'encoding' in elem.attrib:
            self.current_hb[self.I_HEADERS_ENCODING] = elem.attrib['encoding']
        self.states.append(self.S_HEADERS)

    def headers_end(self, elem):
        self.common_headers_body_end(elem, self.I_HEADERS, self.I_HEADERS_ENCODING)

    def body_start(self, elem):
        if 'encoding' in elem.attrib:
            self.current_hb[self.I_BODY_ENCODING] = elem.attrib['encoding']
        self.states.append(self.S_BODY)

    def body_end(self, elem):
        self.common_headers_body_end(elem, self.I_BODY, self.I_BODY_ENCODING)

    def common_headers_body_end(self, elem, i_content, i_encoding):
        content = elem.text
        if content is None:
            content = b''
        else:
            encoding = self.current_hb[i_encoding]
            if 'none' == encoding:
                content = content.encode('utf-8')
            elif 'base64' == encoding:
                content = base64.b64decode(content)
            else:
                raise Exception('unrecognized encoding: %s' % (encoding))

        self.current_hb[i_content] = content
        self.states.pop()
        
    def analysis_start(self, elem):
        self.states.append(self.S_ANALYSIS)

    def analysis_end(self, elem):
        self.states.pop()

    def cookies_start(self, elem):
        self.states.append(self.S_COOKIES)

    def cookies_end(self, elem):
        self.states.pop()

    def cookie_start(self, elem):
        self.states.append(self.S_COOKIE)
        self.current_cookie = {'raw':''}

    def cookie_end(self, elem):
        self.states.pop()
        raw_cookie = self.current_cookie.get('raw')
        return ('COOKIE', raw_cookie)

    def cookie_xml_element_start(self, elem):
        self.states.append(self.S_COOKIE_XML_ELEMENT)

    def cookie_xml_element_end(self, elem):
        content = elem.text
        if not content:
            content = ''
        encoding = 'none'
        if 'encoding' in elem.attrib:
            encoding = elem.attrib['encoding']
        if 'none' == encoding:
            self.current_cookie[elem.tag] = content
        elif 'base64' == encoding:
            self.current_cookie[elem.tag] = base64.b64decode(content).decode('utf-8','ignore')
        else:
            raise Exception('unrecognized encoding: %s' % (encoding))
        self.states.pop()

    def request_xml_element_start(self, elem):
        self.states.append(self.S_REQUEST_XML_ELEMENT)

    def response_xml_element_start(self, elem):
        self.states.append(self.S_RESPONSE_XML_ELEMENT)

    def analysis_xml_element_start(self, elem):
        self.states.append(self.S_ANALYSIS_XML_ELEMENT)

    def xml_element_end(self, elem):
        self.current[elem.tag] = elem.text
        self.states.pop()

    def xml_encoded_element_end(self, elem):
        content = elem.text
        if not content:
            content = ''
        encoding = 'none'
        if 'encoding' in elem.attrib:
            encoding = elem.attrib['encoding']
        if 'none' == encoding:
            self.current[elem.tag] = content
        elif 'base64' == encoding:
            self.current[elem.tag] = base64.b64decode(content).decode('utf-8','ignore')
        else:
            raise Exception('unrecognized encoding: %s' % (encoding))
        self.states.pop()

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            event, elem = next(self.iterator)
            tag = elem.tag
            try:
                state = self.states[-1]
                transitions = self.state_table[state]
                for transition in transitions:
                    if transition[0] == event and transition[1] == tag:
                        func = transition[2]
                        results = func(elem)
                        if results:
                            return results
                        break
                else:
                    raise Exception('Invalid element: state=%s, event=%s, elem=%s' % (state, event, elem.tag))

            except StopIteration:
                self.source.close()
                raise
            except Exception as error:
                self.source.close()
                raise Exception('Internal error: state=%s, event=%s, elem=%s\n%s' % (state, event, elem.tag, traceback.format_exc(error)))

if '__main__' == __name__:
    # test code
    filename = sys.argv[1]
    count = 0
    for result in raft_parse_xml(filename):
        print(result)
        count += 1

    print(('processed count: %d' % (count)))

