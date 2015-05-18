#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2011-2013 RAFT Team
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
# Classes to support parsing Burp logs and state files
import re, time, struct
from urllib import parse as urlparse
import zipfile
import string
import logging, traceback
import base64
from io import StringIO
import bz2
import lzma
import sys

class BurpUtil():
    def __init__(self):
        self.re_content_type = re.compile(br'^Content-Type:\s*([-_+0-9a-z.]+/[-_+0-9a-z.]+(?:\s*;\s*\S+=\S+)*)\s*$', re.I)
        self.re_request = re.compile(br'^(\S+)\s+((?:https?://(?:\S+\.)+\w+(?::\d+)?)?/.*)\s+HTTP/\d+\.\d+\s*$', re.I)
        self.re_response = re.compile(br'^HTTP/\d+\.\d+\s+(\d{3}).*\s*$', re.M)
        self.re_date = re.compile(br'^Date:\s*(\w+,.*\w+)\s*$', re.I)

    def split_request_block(self, request):
        request_headers, request_body = self.split_block(request)
        return (request_headers, request_body)

    def split_response_block(self, response):
        response_headers, response_body = self.split_block(response)
        m = self.re_response.match(response_headers)
        if m and b'100' == m.group(1):
            # TODO: decide if this is best way to handle
            actual_response_headers, actual_response_body = self.split_block(response_body)
            m = self.re_response.match(actual_response_headers)
            if m:
                return (response_headers + actual_response_headers, actual_response_body)
        return (response_headers, response_body)

    def split_block(self, block):
        c = 4
        n = block.find(b'\r\n\r\n')
        if -1 == n:
            c = 2
            block.find(b'\n\n')
        if -1 == n:
            n = len(block)
            c = 0
        return (block[0:n+c], block[n+c:])

    def get_content_type(self, headers):
        content_type = b''
        for line in headers.splitlines():
            m = self.re_content_type.search(line)
            if m:
                content_type = m.group(1)
                break
        return content_type

    def parse_method_url(self, request):
        method, url = b'', b''

        # get method from request header
        headers = request[0]
        n = headers.find(b'\n')
        if n != -1:
            line = headers[0:n]
            m = self.re_request.search(line)
            if m:
                method = m.group(1)
                url = m.group(2)

        return method, url

    def parse_status_content_type_datetime(self, response):
        status, content_type, datetime = b'', b'', b''
        # get status and content_type from response headers
        if response and response[0]:
            headers = response[0]
            first = True
            for line in headers.splitlines():
                if first:
                    first = False
                    m = self.re_response.match(line)
                    if m:
                        status = m.group(1)
                else:
                    m = self.re_content_type.match(line)
                    if m:
                        content_type = m.group(1)
                    else:
                        m = self.re_date.match(line)
                        if m:
                            datetime = m.group(1)
        
        return (status, content_type, datetime)

    def normalize_results(self, origin, host, hostip, url, status, datetime, request, response, method, content_type, extra):
        host = (host or b'').decode('utf-8', 'ignore')
        hostip = (hostip or b'').decode('ascii', 'ignore')
        url = (url or b'').decode('utf-8', 'ignore')
        method = (method or b'').decode('ascii', 'ignore')
        if isinstance(status, int):
            pass
        else:
            status = (status or b'').decode('ascii', 'ignore')
        if isinstance(datetime, str):
            pass
        else:
            datetime = (datetime or b'').decode('ascii', 'ignore')
        content_type = (content_type or b'').decode('ascii', 'ignore')
        if 'notes' in extra:
            # TODO: should allow for binary
            extra['notes'] = (extra['notes'] or b'').decode('utf-8', 'ignore')

        return origin, host, hostip, url, status, datetime, request, response, method, content_type, extra

class burp_parse_state():
    """ Parses Burp saved state file into request and result data """

    S_INITIAL = 1
    S_VERSION = 2
    S_BEGIN_STATE = 10
    S_END_STATE = 11
    S_BEGIN_CONFIG = 20
    S_END_CONFIG = 21
    S_BEGIN_TARGET = 30
    S_END_TARGET = 31
    S_BEGIN_SCANNER = 40
    S_END_SCANNER = 41
    S_BEGIN_PROXY = 50
    S_END_PROXY = 51
    S_BEGIN_REPEATER = 60
    S_END_REPEATER = 61
    S_BEGIN_REQUEST_PANEL = 70
    S_END_REQUEST_PANEL = 71
   
    T_INT32 = 0
    T_INT64 = 1
    T_BOOL = 2
    T_STRING = 3
    T_BINSTR = 4
    T_UNKNOWN_5 = 5
    T_TAG = 256

    def __init__(self, burpfile):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Parsing Burp state file: %s' % (burpfile))
        self.util = BurpUtil()

        self.zfile = zipfile.ZipFile(burpfile, 'r')
        for zi in self.zfile.infolist():
            if zi.filename == 'burp':
                self.file = self.zfile.open(zi.filename, 'r')
                break
        else:
            raise Exception

        self.states = []
        self.buffer = b''
        self.state = self.S_INITIAL

    def __iter__(self):
        return self

    def __read_data(self, length):

        data = b''
        if self.buffer:
            # buffered data
            if len(self.buffer) >= length:
                data = self.buffer[0:length]
                self.buffer = self.buffer[length:]
            else:
                data = self.buffer
                self.buffer = b''

        readlen = length - len(data)
        while readlen > 0:
            buf = self.file.read(readlen)
            if not buf:
                self.logger.debug('read to end of file')
                self.file.close()
                raise(StopIteration)
            buflen = len(buf)
            if buflen > readlen:
                data += buf[0:readlen]
                self.buffer = buf[readlen:]
                break
            else:
                data += buf
                readlen -= len(buf)
        return data

    def __read_next_tag(self, begin):
        data = begin
        while True:
            b = self.__read_data(1)
            data += b
            if b'>' == b:
                break
        return data

    def read_next(self):
        return self.__read_next()

    def __read_next(self):
        token = self.__read_data(1)
        if b'<' == token:
            tag = self.__read_next_tag(token)
            return (self.T_TAG, tag)
        else:
            datatype = ord(token)
            if self.T_INT32 == datatype: # 32 bit
                data = self.__read_data(4)
                datavalue = struct.unpack('>L', data)[0]
                return (datatype, datavalue)
            elif self.T_INT64 == datatype: # 64 bit
                data = self.__read_data(8)
                datavalue = struct.unpack('>Q', data)[0]
                return (datatype, datavalue)
            elif self.T_BOOL == datatype: # boolean
                data = self.__read_data(1)
                b = 0 != ord(data)
                return (datatype, b)
            elif self.T_STRING == datatype or self.T_BINSTR == datatype: # string
                data = self.__read_data(4)
                datalen = struct.unpack('>L', data)[0]
                datavalue = self.__read_data(datalen)
                return (datatype, datavalue)
            elif self.T_UNKNOWN_5 == datatype: # not known, maybe empty data/emptry string?
                return (datatype, b'')
            else:
                raise Exception

    def __read_tag(self, tagname = None):
        result = self.__read_next()
        if tagname:
            if self.T_TAG != result[0] or tagname != result[1]:
                self.logger.error('failed on tag read; read: [%d,%s], expected: [%s]' % (result, tagname))
                raise Exception
        else:
            if self.T_TAG != result[0]:
                self.logger.error('failed on tag read; read: [%d,%s]' % (result))
                raise Exception
        self.logger.debug('read tag: [%s]' % (result[1]))
        return result[1]

    def __read_int(self):
        result = self.__read_next()
        if self.T_INT32 != result[0]:
            self.logger.warn('failed on int read; read: [%d,%s]' % (result))
        return result[1]

    def __read_int64(self):
        result = self.__read_next()
        if self.T_INT64 != result[0]:
            self.logger.warn('failed on int64 read; read: [%d,%s]' % (result))
        return result[1]

    def __read_bool(self):
        result = self.__read_next()
        if self.T_BOOL != result[0]:
            self.logger.warn('failed on bool read; read: [%d,%s]' % (result))
        return result[1]

    def __read_string(self):
        result = self.__read_next()
        if self.T_STRING != result[0] and self.T_BINSTR != result[0]:
            self.logger.warn('failed on string read; read: [%d,%s]' % (result))
        return result[1]

    def __read_node_int(self, tagname):
        self.__read_tag(b'<'+tagname+b'>')
        result = self.__read_int()
        self.__read_tag(b'</'+tagname+b'>')
        return result
        
    def __process_version(self):
        version = self.__read_node_int(b'version')
        self.logger.debug('read burp state version: %d', version)

    def __make_url(self, scheme, host, port, path):
        # TODO: consider replacing with urlunsplit
        url = scheme + b'://' + host
        if b'http' == scheme and 80 == port:
            pass
        elif b'https' == scheme and 443 == port:
            pass
        else:
            if isinstance(port, bytes):
                url += b':' + port
            else:
                url += b':' + str(port).encode('ascii')
        if not path.startswith(b'/'):
            url += b'/'
        url += path
        return url

    def __process_url(self):
        port = 80
        https = False
        scheme = b'http'
        path = None
        url = b''
        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and b'</url>' == nextdata[1]):
            if self.T_TAG == nextdata[0]:
                tagname = nextdata[1]
                if b'<https>' == tagname:
                    https = self.__read_bool()
                    if https:
                        scheme = b'https'
                    self.__read_tag(b'</https>')
                elif b'<host>' == tagname:
                    host = self.__read_string()
                    self.__read_tag(b'</host>')
                elif b'<file>' == tagname:
                    path = self.__read_string()
                    self.__read_tag(b'</file>')
                elif b'<port>' == tagname:
                    port = self.__read_int()
                    self.__read_tag(b'</port>')
                else:
                    self.logger.debug('unhandled tag: [%s]' % tagname)
            else:
                self.logger.debug('unhandled value: [%s]' % nextdata[1])

            nextdata = self.__read_next()

        url = self.__make_url(scheme, host, port, path)
        return (url, host)

    def __read_datetime(self):
        millisecs = self.__read_int64()
        dt = millisecs/1000
        return time.asctime(time.localtime(dt))

    def __parse_method_content_type(self, request, response):
        method = b''
        content_type = b''

        # get method from request header
        headers = request[0]
        n = headers.find(b'\n')
        if n != -1:
            line = headers[0:n]
            m = self.util.re_request.search(line)
            if m:
                method = m.group(1)
        
        # get content_type from response headers
        if response and response[0]:
            content_type = self.util.get_content_type(response[0])
        
        return (method, content_type)

    def __process_info(self, url, host):
        hostip = b''
        status = 0
        datetime = b''
        request = None
        response = None
        resplen = -1
        state = None

        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and b'</info>' == nextdata[1]):
            if self.T_TAG == nextdata[0]:
                tagname = nextdata[1]
                if b'<statusCode>' == tagname:
                    status = self.__read_int()
                    self.__read_tag(b'</statusCode>')
                elif b'<responseLength>' == tagname:
                    resplen = self.__read_int()
                    self.__read_tag(b'</responseLength>')
                elif b'<responseLength>' == tagname:
                    resplen = self.__read_int()
                    self.__read_tag(b'</responseLength>')
                elif b'<response>' == tagname:
                    response = self.util.split_response_block(self.__read_string())
                    self.__read_tag(b'</response>')
                elif b'<request>' == tagname:
                    request = self.util.split_request_block(self.__read_string())
                    self.__read_tag(b'</request>')
                elif b'<state>' == tagname:
                    state = self.__read_int()
                    self.__read_tag(b'</state>')
                elif  b'<time>' == tagname:
                    datetime = self.__read_datetime()
                    self.__read_tag(b'</time>')
                else:
                    self.logger.debug('unhandled tag: [%s]' % tagname)
            else:
                self.logger.debug('unhandled value: [%s]' % nextdata[1])

            nextdata = self.__read_next()

        if not request:
            return None

        method, content_type = self.__parse_method_content_type(request, response)
        return self.util.normalize_results('TARGET', host, hostip, url, status, datetime, request, response, method, content_type, {})
        
    def __process_item(self):
        nextdata = self.__read_next()
        result = None
        url = None
        host = None
        while not (self.T_TAG == nextdata[0] and b'</item>' == nextdata[1]):
            if (self.T_TAG == nextdata[0] and b'<url>' == nextdata[1]):
                url, host = self.__process_url()
            elif (self.T_TAG == nextdata[0] and b'<info>' == nextdata[1]):
                if result:
                    raise Exception
                result = self.__process_info(url, host)
            nextdata = self.__read_next()
        return result

    def __process_historyItem(self):

        hostip = b''
        host = b''
        status = 0
        datetime = b''
        request = None
        response = None
        resplen = -1

        url = None

        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and b'</historyItem>' == nextdata[1]):
            if self.T_TAG == nextdata[0]:
                tagname = nextdata[1]
                if b'<url>' == tagname:
                    url, host = self.__process_url()
                elif b'<statusCode>' == tagname:
                    status = self.__read_int()
                    self.__read_tag(b'</statusCode>')
                elif b'<ipAddress>' == tagname:
                    hostip = self.__read_string()
                    self.__read_tag(b'</ipAddress>')
                elif  b'<time>' == tagname:
                    datetime = self.__read_datetime()
                    self.__read_tag(b'</time>')
                elif b'<originalResponse>' == tagname:
                    response = self.util.split_response_block(self.__read_string())
                    self.__read_tag(b'</originalResponse>')
                elif b'<originalRequest>' == tagname:
                    request = self.util.split_request_block(self.__read_string())
                    self.__read_tag(b'</originalRequest>')
                elif b'<editedResponse>' == tagname:
                    response = self.util.split_response_block(self.__read_string())
                    self.__read_tag(b'</editedResponse>')
                elif b'<editedRequest>' == tagname:
                    request = self.util.split_request_block(self.__read_string())
                    self.__read_tag(b'</editedRequest>')
                elif b'<responseLength>' == tagname:
                    resplen = self.__read_int()
                    self.__read_tag(b'</responseLength>')
                else:
                    self.logger.debug('unhandled tag: [%s]' % tagname)
            else:
                self.logger.debug('unhandled value: [%s]' % nextdata[1])

            nextdata = self.__read_next()

        if not request:
            return None

        method, content_type = self.__parse_method_content_type(request, response)
        return self.util.normalize_results('PROXY', host, hostip, url, status, datetime, request, response, method, content_type, {})

    def __process_repeater_historyItem(self):

        hostip = b''
        host = b''
        status = 0
        datetime = b''
        request = None
        response = None
        resplen = -1

        url = None

        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and b'</historyItem>' == nextdata[1]):
            if self.T_TAG == nextdata[0]:
                tagname = nextdata[1]
                if b'<url>' == tagname:
                    url, host = self.__process_url()
                elif b'<statusCode>' == tagname:
                    status = self.__read_int()
                    self.__read_tag(b'</statusCode>')
                elif b'<ipAddress>' == tagname:
                    hostip = self.__read_string()
                    self.__read_tag(b'</ipAddress>')
                elif  b'<time>' == tagname:
                    datetime = self.__read_datetime()
                    self.__read_tag(b'</time>')
                elif b'<response>' == tagname:
                    response = self.util.split_response_block(self.__read_string())
                    self.__read_tag(b'</response>')
                elif b'<request>' == tagname:
                    request = self.util.split_request_block(self.__read_string())
                    self.__read_tag(b'</request>')
                elif b'<responseLength>' == tagname:
                    resplen = self.__read_int()
                    self.__read_tag(b'</responseLength>')
                else:
                    self.logger.debug('unhandled tag: [%s]' % tagname)
            else:
                self.logger.debug('unhandled value: [%s]' % nextdata[1])

            nextdata = self.__read_next()

        if not request:
            return None

        method, content_type = self.__parse_method_content_type(request, response)
        return self.util.normalize_results('REPEATER', host, hostip, url, status, datetime, request, response, method, content_type, {})

    def __process_requestPanel(self):
        nextdata = self.__read_next()
        result = None
        while not (self.T_TAG == nextdata[0] and b'</requestPanel>' == nextdata[1]):
            if (self.T_TAG == nextdata[0] and b'<historyItem>' == nextdata[1]):
                result = self.__process_repeater_historyItem()
            nextdata = self.__read_next()
        return result

    def __process_issue(self):

        hostip = b''
        host = b''
        status = 0
        datetime = b''
        request = None
        response = None
        notes = b''
        resplen = -1

        url = None

        # TODO: determine if better heuristic
        # issue can contain multiple response/request sets
        found_r = False

        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and b'</issue>' == nextdata[1]):
            if self.T_TAG == nextdata[0]:
                tagname = nextdata[1]
                if found_r:
                    pass
                elif b'<url>' == tagname:
                    url, host = self.__process_url()
                elif b'<statusCode>' == tagname:
                    status = self.__read_int()
                    self.__read_tag(b'</statusCode>')
                elif b'<ipAddress>' == tagname:
                    hostip = self.__read_string()
                    self.__read_tag(b'</ipAddress>')
                elif b'<id>' == tagname:
                    notes = self.__read_string()
                    self.__read_tag(b'</id>')
                elif  b'<time>' == tagname:
                    datetime = self.__read_datetime()
                    self.__read_tag(b'</time>')
                elif b'<response>' == tagname:
                    response = self.util.split_response_block(self.__read_string())
                    self.__read_tag(b'</response>')
                elif b'<request>' == tagname:
                    request = self.util.split_request_block(self.__read_string())
                    self.__read_tag(b'</request>')
                elif b'<responseLength>' == tagname:
                    resplen = self.__read_int()
                    self.__read_tag(b'</responseLength>')
                elif b'</r>' == tagname:
                    found_r = True
                else:
                    self.logger.debug('unhandled tag: [%s]' % tagname)
            else:
                self.logger.debug('unhandled value: [%s]' % nextdata[1])

            nextdata = self.__read_next()

        if not request:
            return None

        method, content_type = self.__parse_method_content_type(request, response)
        return self.util.normalize_results('SCANNER', host, hostip, url, status, datetime, request, response, method, content_type, {'notes':notes, 'confirmed':True}) # TODO: confirmed hard-coded

    def __process_hps(self):
        # ignore
        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and b'</hps>' == nextdata[1]):
            nextdata = self.__read_next()
        return None

    def __read_until_tag(self, tagname):
        # ignore
        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and tagname == nextdata[1]):
            nextdata = self.__read_next()

    def __next__(self):
        while True:
            if self.S_INITIAL == self.state:
                self.__process_version()
                self.state = self.S_VERSION
            elif self.state in (self.S_VERSION, self.S_END_STATE):
                nexttag = self.__read_tag()
                if b'<config>' == nexttag:
                    self.state = self.S_BEGIN_CONFIG
                elif b'<state>' == nexttag:
                    self.state = self.S_BEGIN_STATE
                else:
                    raise Exception('unhandled tag in %s state: %s' % (self.state, nexttag.decode('utf-8')))
            elif self.state in (self.S_BEGIN_STATE, self.S_END_TARGET, self.S_END_PROXY, self.S_END_SCANNER, self.S_END_REPEATER):
                nexttag = self.__read_tag()
                if b'<target>' == nexttag:
                    self.state = self.S_BEGIN_TARGET
                elif b'<proxy>' == nexttag:
                    self.state = self.S_BEGIN_PROXY
                elif b'<scanner>' == nexttag:
                    self.state = self.S_BEGIN_SCANNER
                elif b'<repeater>' == nexttag:
                    self.state = self.S_BEGIN_REPEATER
                elif b'</state>' == nexttag:
                    self.state = self.S_END_STATE
                else:
                    raise Exception('unhandled tag in %s state: %s' % (self.state, nexttag.decode('utf-8')))
            elif self.S_BEGIN_TARGET == self.state:
                nexttag = self.__read_tag()
                if b'<item>' == nexttag:
                    result = self.__process_item()
                    if result:
                        return result
                elif b'</target>' == nexttag:
                    self.state = self.S_END_TARGET
                else:
                    raise Exception('unhandled tag in S_BEGIN_TARGET state: %s' % (nexttag.decode('utf-8')))
            elif self.S_BEGIN_PROXY == self.state:
                nexttag = self.__read_tag()
                if b'<historyItem>' == nexttag:
                    result = self.__process_historyItem()
                    if result:
                        return result
                elif b'<wsHistoryItem>' == nexttag:
                    # TODO: XXX implement
                    self.__read_until_tag(b'</wsHistoryItem>')
                elif b'</proxy>' == nexttag:
                    self.state = self.S_END_PROXY
                else:
                    raise Exception('unhandled tag in S_BEGIN_PROXY state: %s' % (nexttag.decode('utf-8')))
            elif self.S_BEGIN_SCANNER == self.state:
                nexttag = self.__read_tag()
                if b'<issue>' == nexttag:
                    result = self.__process_issue()
                    if result:
                        return result
                elif b'<paused>' == nexttag:
                    paused = self.__read_bool()
                    self.__read_tag(b'</paused>')
                elif b'<hps>' == nexttag:
                    self.__process_hps()
                elif b'<queueitem>' == nexttag:
                    self.__read_until_tag(b'</queueitem>')
                elif b'<asi>' == nexttag:
                    self.__read_until_tag(b'</asi>')
                elif b'<has>' == nexttag:
                    self.__read_until_tag(b'</has>')
                elif b'</scanner>' == nexttag:
                    self.state = self.S_END_SCANNER
                else:
                    raise Exception('unhandled tag in S_BEGIN_SCANNER state: %s' % (nexttag.decode('utf-8')))
            elif self.state in (self.S_BEGIN_REPEATER, self.S_END_REQUEST_PANEL):
                nexttag = self.__read_tag()
                if b'<requestPanel>' == nexttag:
                    self.state = self.S_BEGIN_REQUEST_PANEL
                elif b'</repeater>' == nexttag:
                    self.state = self.S_END_REPEATER
                else:
                    raise Exception('unhandled tag in %s state: %s' % (self.state, nexttag.decode('utf-8')))
            elif self.S_BEGIN_REQUEST_PANEL == self.state:
                nexttag = self.__read_tag()
                if b'<tabCaption>' == nexttag:
                    self.__read_until_tag(b'</tabCaption>')
                elif b'<historyIndex>' == nexttag:
                    self.__read_until_tag(b'</historyIndex>')
                elif b'<displayedService>' == nexttag:
                    self.__read_until_tag(b'</displayedService>')
                elif b'<displayedRequest>' == nexttag:
                    self.__read_until_tag(b'</displayedRequest>')
                elif b'<historyItem>' == nexttag:
                    result = self.__process_repeater_historyItem()
                    if result:
                        return result
                elif b'<wsHistoryItem>' == nexttag:
                    # TODO: XXX implement
                    self.__read_until_tag(b'</wsHistoryItem>')
                elif b'</requestPanel>' == nexttag:
                    self.state = self.S_END_REQUEST_PANEL
                else:
                    raise Exception('unhandled tag in S_BEGIN_REQUEST_PANEL state: %s' % (nexttag.decode('utf-8')))
            elif self.S_BEGIN_CONFIG == self.state:
                self.__read_until_tag(b'</config>')
                self.state = self.S_END_CONFIG
            elif self.S_END_CONFIG == self.state:
                self.logger.debug('reached end configuration state')
                self.file.close()
                raise(StopIteration)
            else:
                raise Exception

class burp_dump_state(burp_parse_state):
    """ For exploration of state content """

    def __next__(self):
        return burp_parse_state.read_next(self)

class burp_parse_log():
    """ Parses Burp log file into request and result data """

    DELIMITER = b'======================================================'

    S_INITIAL = 1
    S_DELIMITER = 2
    S_BURP_HEADER = 3
    S_HTTP_REQUEST = 4
    S_HTTP_RESPONSE = 5

    def __init__(self, burpfile):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Parsing Burp log file: %s' % (burpfile))
        self.util = BurpUtil()

        self.re_burp = re.compile(br'^(\d{1,2}:\d{1,2}:\d{1,2}\s+(?:AM|PM))\s+(https?://(?:\S+\.)*\w+:\d+)(?:\s+\[((?:\d{1,3}\.){3}\d{1,3})\])?\s*$', re.I)
        self.re_content_length = re.compile(br'^Content-Length:\s*(\d+)\s*$', re.I)
        self.re_chunked = re.compile(br'^Transfer-Encoding:\s*chunked\s*$', re.I)
        self.re_chunked_length = re.compile(b'^[a-f0-9]+$', re.I)
        self.re_date = re.compile(br'^Date:\s*(\w+,.*\w+)\s*$', re.I)

        if isinstance(burpfile, bytes):
            burpfile = burpfile.decode('utf-8')
        if isinstance(burpfile, str):
            if burpfile.endswith('.bz2'):
                self.file = bz2.BZ2File(burpfile, 'rb')
            elif burpfile.endswith('.xz'):
                self.file = lzma.LZMAFile(burpfile, 'rb')
            else:
                self.file = open(burpfile, 'rb')
        else:
            # assume file like object
            self.file = burpfile

        self.state = self.S_INITIAL
        self.peaked = False
        self.peakbuf = b''

    def __iter__(self):
        return self

    def __synthesize_url(self, hosturl, requrl):
        p1 = urlparse.urlsplit(hosturl)
        p2 = urlparse.urlsplit(requrl)

        if p2.scheme:
            scheme = p2.scheme
        else:
            scheme = p1.scheme
        
        if p2.netloc:
            netloc = p2.netloc
            host = p2.hostname
        else:
            netloc = p1.netloc
            host = p1.hostname

        # TODO: maybe change this to use hostname and port?
        if b'http' == scheme:
            netloc = netloc.replace(b':80',b'')
        elif b'https' == scheme:
            netloc = netloc.replace(b':443',b'')
        
        url = scheme + b'://' + netloc + p2.path
        if p2.query:
            url += b'?' + p2.query
        if p2.fragment:
            url += b'#' + p2.fragment

        return url, host

    def __synthesize_date(self, burptime, datetime):
        if not burptime and not datetime:
            return b''
        if datetime:
            try:
                tm = time.strptime(str(datetime,'ascii'), '%a, %d %b %Y %H:%M:%S %Z')
                tm = time.localtime(time.mktime(tm)-time.timezone)
            except Exception as e:
                self.logger.debug('Failed parsing datetime [%s]: %s' % (datetime, e))
        else:
            tm = time.localtime()

        # use today's date
        # TODO: improve
        n = burptime.rfind(b' ')
        hms = burptime[0:n].split(b':')
        ampm = burptime[n+1:]

        h = int(hms[0])
        if b'PM' == ampm:
            if h < 12:
                h += 12
        elif b'AM' == ampm:
            if h == 12:
                h = 0

        m = int(hms[1])
        s = int(hms[2])
        if h > tm.tm_hour:
            # assume this was yesterday
            tm = time.localtime(time.mktime(tm)-60*60*24)

        reqtm = time.mktime((tm.tm_year, tm.tm_mon, tm.tm_mday, h, m, s, tm.tm_wday, tm.tm_yday, tm.tm_isdst))
        return bytes(time.asctime(time.localtime(reqtm)), 'ascii')

    def __peak_line(self):
        line = self.file.readline()
        if not line:
            self.logger.debug('reached end of file')
            self.file.close()
            raise(StopIteration)
        self.peakbuf = line
        self.peaked = True
        return line
        
    def __read_line(self):
        if self.peaked:
            line = self.peakbuf
            self.peaked = False
        else:
            line = self.file.readline()
            if not line:
                self.logger.debug('reached end of file')
                self.file.close()
                raise(StopIteration)
        return line

    def __read_data(self, length):
        data = self.file.read(length)
        if len(data) != length:
            raise Exception
        return data

    def __read_chunked(self, line):
        data = b''
        while line:
            length = int(line, 16)
            if 0 == length:
                break
            data += self.file.read(length)
            line = self.__read_line().rstrip()

        line = self.__read_line().rstrip()
        if 0 != len(line):
            self.logger.warning('failed to read chunked data: %s' % (line))

        return data

    def __process_block(self, firstline, skipbody = False):
        headers = firstline
        body = b''
        datetime = b''
        content_type = b''
        content_length = -1
        chunked = False
        while True:
            # TODO: this does not handle degenerate header conditions
            line = self.__read_line()
            headers += line
            if 0 == len(line.rstrip()):
                # TODO: handle 100 Continue
                break
            m = self.re_content_length.search(line)
            if m:
                content_length = int(m.group(1))
            elif self.re_chunked.search(line):
                chunked = True
            else:
                m = self.re_date.search(line)
                if m:
                    datetime = m.group(1)
                else:
                    m = self.util.re_content_type.search(line)
                    if m:
                        content_type = m.group(1)

        readbody = False
        if skipbody:
            pass
        elif chunked:
            line = self.__read_line().rstrip()
            firstline = line.rstrip()
            if self.re_chunked_length.match(firstline):
                body = self.__read_chunked(firstline)
            else:
                self.logger.warning('expected chunked data, but got: %s' % (firstline))
                readbody = True
        elif -1 != content_length:
            body = self.__read_data(content_length)
        else:
            readbody = True

        if readbody:
            # TODO: handle binary content better ...
            while True:
                if self.__peak_line().startswith(self.DELIMITER):
                    break
                line = self.__read_line()
                if 0 == len(line.rstrip()) and self.__peak_line().startswith(self.DELIMITER):
                    # empty trailing line before delimiter
                    break
                body += line

        return (headers, body, datetime, content_type)
        
    def __process_request(self, method, firstline):
        return self.__process_block(firstline)

    def __process_response(self, method, firstline):
        return self.__process_block(firstline, b'HEAD' == method.upper())
        
    def __next__(self):
        have_burp_header, have_http_request, have_http_response = False, False, False
        while True:
            line = self.__read_line()
            if self.S_INITIAL == self.state:
                line = line.rstrip()
                if not line:
                    pass
                elif self.DELIMITER == line:
                    self.state = self.S_DELIMITER
                else:
                    self.logger.debug('Ignoring leading garbage: %s' % (line))
            elif self.S_DELIMITER == self.state:

                if have_burp_header and have_http_request:
                    # check response header
                    m = self.util.re_response.search(line)
                    if m:
                        status = m.group(1)
                        temp = self.__process_response(method, line)
                        response = [temp[0], temp[1]]
                        datetime = self.__synthesize_date(burptime, temp[2])
                        content_type = temp[3]
                        have_http_response = True
                        self.state = self.S_HTTP_RESPONSE
                        continue

                if have_burp_header:
                    # check request header
                    m = self.util.re_request.search(line)
                    if m:
                        method = m.group(1)
                        requrl = m.group(2)
                        temp = self.__process_request(method, line)
                        request = [temp[0], temp[1]]
                        have_http_request = True
                        self.state = self.S_HTTP_REQUEST
                        continue

                # check burp header
                m = self.re_burp.search(line)
                if m:
                    burptime = m.group(1)
                    hosturl = m.group(2)
                    hostip = m.group(3)
                    if not hostip:
                        parsed = urlparse.urlsplit(hosturl)
                        hostip = parsed.netloc[0:parsed.netloc.find(b':')]
                    have_burp_header = True
                    have_http_request, have_http_response = False, False
                    request, response = None, None
                    url = hosturl
                    datetime = b''
                    status = 0
                    method = b''
                    requrl = b''
                    content_type = b''
                    self.state = self.S_BURP_HEADER
                    continue

            elif self.state in (self.S_BURP_HEADER, self.S_HTTP_REQUEST, self.S_HTTP_RESPONSE):
                line = line.rstrip()
                if not line:
                    pass
                elif self.DELIMITER == line:
                    self.state = self.S_DELIMITER
                    if have_http_request and have_http_response:
                        url, host = self.__synthesize_url(hosturl, requrl)
                        return self.util.normalize_results('LOG', host, hostip, url, status, datetime, request, response, method, content_type, {})
                else:
                    self.logger.debug('Garbage: %s' % (line))
            else:
                raise Exception

class burp_parse_xml():
    """ parse Burp broken XML format """

    S_INITIAL = 1
    S_ITEMS = 2
    S_ITEM = 3

    S_ITEM_XML_ELEMENT = 101

    class BurpBrokenXml(object):
        def __init__(self, burpfile):

            if isinstance(burpfile, bytes):
                burpfile = burpfile.decode('utf-8')
            if isinstance(burpfile, str):
                if burpfile.endswith('.bz2'):
                    self.xmlfile = bz2.BZ2File(burpfile, 'rb')
                elif burpfile.endswith('.xz'):
                    self.xmlfile = lzma.LZMAFile(burpfile, 'rb')
                else:
                    self.xmlfile = open(burpfile, 'rb')
            else:
                # assume file-like object
                self.xmlfile = burpfile

            self.buffer = b''
            self.re_nonprintable = re.compile(bytes('[^%s]' % re.escape('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r'),'ascii'))
            self.entity_encode = lambda m: bytes('&#x%02X;' % ord(m.group(0)),'ascii')
            self.name = b'<BurpBrokenXml>'
            self.closed = False
            self.last_response = b''
            self.buffer = b''

        def close(self):
            if not self.closed:
                self.xmlfile.close()

        def read(self, size = -1):
            if self.closed and not self.buffer:
                return None

            raw = None
            if not self.closed:
                raw = self.xmlfile.read(size)
            if not raw:
                if not self.closed:
                    self.xmlfile.close()
                    self.closed = True
                response = None
                if self.buffer:
                    response = self.buffer
                    self.buffer = b''
            else:
                fixed = self.re_nonprintable.sub(self.entity_encode, raw)
                if self.buffer:
                    response = self.buffer + fixed
                    self.buffer = b''
                else:
                    response = fixed
            if -1 != size and response:
                rlen = len(response)
                if rlen > size:
                    # TODO: avoid splitting encoded entities across buffers ?
                    apos = response.rfind(b'&', size - 6, size)
                    if apos != -1:
                        self.buffer = response[apos:]
                        response = response[0:apos]
                    else:
                        self.buffer = response[size:]
                        response = response[0:size]
            self.last_response = response
#            print('~~~request=%d, return=%d, buffer=%d~~~' % (size, len(response), len(self.buffer)))
            return response
            
    def __init__(self, burpfile):

        self.re_encoded = re.compile(r'&#[xX]([0-9a-fA-F]{2});')
        self.decode_entity = lambda m: '%c' % (int(m.group(1),16))

        self.source = burp_parse_xml.BurpBrokenXml(burpfile)

        # TODO: lazy ...
        from lxml import etree
        # http://effbot.org/zone/element-iterparse.htm#incremental-parsing
        self.context = etree.iterparse(self.source, events=('start', 'end'))
        self.iterator = iter(self.context)
        self.root = None

        self.util = BurpUtil()

        self.version = 1
        self.states = [self.S_INITIAL]
        self.state_table = {
            self.S_INITIAL : (
                ('start', 'items', self.items_start),
                ),
            self.S_ITEMS : (
                ('start', 'item', self.item_start),
                ('end', 'items', self.items_end),
                ),
            self.S_ITEM : (
                ('start', 'time', self.item_xml_element_start),
                ('start', 'url', self.item_xml_element_start),
                ('start', 'host', self.item_host_start),
                ('start', 'port', self.item_xml_element_start),
                ('start', 'protocol', self.item_xml_element_start),
                ('start', 'method', self.item_xml_element_start),
                ('start', 'path', self.item_xml_element_start),
                ('start', 'extension', self.item_xml_element_start),
                ('start', 'request', self.item_xml_element_start),
                ('start', 'status', self.item_xml_element_start),
                ('start', 'responselength', self.item_xml_element_start),
                ('start', 'mimetype', self.item_xml_element_start),
                ('start', 'response', self.item_xml_element_start),
                ('start', 'comment', self.item_xml_element_start),
                ('end', 'item', self.item_end),
                ),
            self.S_ITEM_XML_ELEMENT : (
                ('end', 'time', self.xml_element_end),
                ('end', 'url', self.xml_element_end),
                ('end', 'host', self.xml_element_end),
                ('end', 'port', self.xml_element_end),
                ('end', 'protocol', self.xml_element_end),
                ('end', 'method', self.xml_element_end),
                ('end', 'path', self.xml_element_end),
                ('end', 'extension', self.xml_element_end),
                ('end', 'request', self.xml_element_end_base64),
                ('end', 'status', self.xml_element_end),
                ('end', 'responselength', self.xml_element_end),
                ('end', 'mimetype', self.xml_element_end),
                ('end', 'response', self.xml_element_end_base64),
                ('end', 'comment', self.xml_element_end),
                ),
            }
        self.default_values = (
            ('time', ''),
            ('url', ''),
            ('host', ''),
            ('hostip', ''),
            ('port', ''),
            ('protocol', ''),
            ('method', ''),
            ('path', ''),
            ('extension', ''),
            ('request', ''),
            ('status', ''),
            ('responselength', ''),
            ('mimetype', ''),
            ('response', ''),
            ('comment', ''),
            )

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
        datetime = cur['time']
        method = cur['method']
        request = self.util.split_request_block(cur['request'])
        response = self.util.split_response_block(cur['response'])
        if response and response[0]:
            content_type = self.util.get_content_type(response[0])
        else:
            # TODO: fix me
#            content_type = self.util.content_type_from_mimetype(cur['mimetype'])
            content_type = cur['mimetype']
            pass

        if type(content_type) is bytes:
            content_type = str(content_type, 'utf-8', 'ignore')

        return ('XML', host, hostip, url, status, datetime, request, response, method, content_type, {'notes':cur['comment']})

    def items_start(self, elem):
        self.root = elem
        self.states.append(self.S_ITEMS)

    def items_end(self, elem):
        raise(StopIteration)

    def item_start(self, elem):
        self.current = {}
        for n, v in self.default_values:
            self.current[n] = v
        self.states.append(self.S_ITEM)

    def item_end(self, elem):
        elem.clear()
        self.states.pop()
        return self.make_results()

    def item_xml_element_start(self, elem):
        self.states.append(self.S_ITEM_XML_ELEMENT)

    def item_host_start(self, elem):
        self.states.append(self.S_ITEM_XML_ELEMENT)
        if 'ip' in elem.attrib:
            self.current['hostip'] = elem.attrib['ip']

    def xml_element_end(self, elem):
        if elem.text is None:
            self.current[elem.tag] = ''
        else:
            self.current[elem.tag] = self.re_encoded.sub(self.decode_entity, elem.text)
        self.states.pop()

    def xml_element_end_base64(self, elem):
        if elem.text is None:
            self.current[elem.tag] = b''
        elif 'base64' in elem.attrib and 'true' == elem.attrib['base64']:
            self.current[elem.tag] = base64.b64decode(elem.text)
        else:
            self.current[elem.tag] = bytes(self.re_encoded.sub(self.decode_entity, elem.text), 'utf-8') # TODO: or ascii?
        self.states.pop()
            
    def __iter__(self):
        return self

    def __next__(self):
        event, elem, tag, state = None, None, None, None
        while True:
            try:
                event, elem = next(self.iterator)
                tag = elem.tag
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
                print(('***%s***\n^^^%s^^^' % (self.source.last_response, self.source.buffer)))
                self.source.close()
                raise Exception('Internal error: state=%s, event=%s, elem=%s\n%s' % (state, event, elem.tag, traceback.format_exc(error)))

class burp_parse_vuln_xml():
    """ parse Burp broken XML format """

    S_INITIAL = 1
    S_ISSUES = 2
    S_ISSUE = 3
    S_REQUESTRESPONSE = 4

    S_ISSUE_XML_ELEMENT = 101
    S_REQUESTRESPONSE_XML_ELEMENT = 102
            
    def __init__(self, burpfile):

        self.re_encoded = re.compile(r'&#[xX]([0-9a-fA-F]{2});')
        self.decode_entity = lambda m: '%c' % (int(m.group(1),16))
        self.re_clean_host = re.compile(r'^https?://')

        self.source = burp_parse_xml.BurpBrokenXml(burpfile)

        # TODO: lazy ...
        from lxml import etree
        # http://effbot.org/zone/element-iterparse.htm#incremental-parsing
        self.context = etree.iterparse(self.source, events=('start', 'end'), huge_tree = True)
        self.iterator = iter(self.context)
        self.root = None

        self.util = BurpUtil()

        self.version = 1
        self.states = [self.S_INITIAL]
        self.state_table = {
            self.S_INITIAL : (
                ('start', 'issues', self.issues_start),
                ),
            self.S_ISSUES : (
                ('start', 'issue', self.issue_start),
                ('end', 'issues', self.issues_end),
                ),
            self.S_ISSUE : (
                ('start', 'serialNumber', self.issue_xml_element_start),
                ('start', 'type', self.issue_xml_element_start),
                ('start', 'name', self.issue_xml_element_start),
                ('start', 'host', self.issue_host_start),
                ('start', 'path', self.issue_xml_element_start),
                ('start', 'location', self.issue_xml_element_start),
                ('start', 'severity', self.issue_xml_element_start),
                ('start', 'confidence', self.issue_xml_element_start),
                ('start', 'issueBackground', self.issue_xml_element_start),
                ('start', 'remediationBackground', self.issue_xml_element_start),
                ('start', 'issueDetail', self.issue_xml_element_start),
                ('start', 'remediationDetail', self.issue_xml_element_start),
                ('start', 'requestresponse', self.requestresponse_start),
                ('end', 'issue', self.issue_end),
                ),
            self.S_REQUESTRESPONSE : (
                ('start', 'request', self.requestresponse_xml_element_start),
                ('start', 'response', self.requestresponse_xml_element_start),
                ('start', 'responseRedirected', self.requestresponse_xml_element_start),
                ('end', 'requestresponse', self.requestresponse_end),
                ),
            self.S_ISSUE_XML_ELEMENT : (
                ('end', 'serialNumber', self.xml_element_end),
                ('end', 'type', self.xml_element_end),
                ('end', 'name', self.xml_element_end),
                ('end', 'host', self.xml_element_end),
                ('end', 'path', self.xml_element_end),
                ('end', 'location', self.xml_element_end),
                ('end', 'severity', self.xml_element_end),
                ('end', 'confidence', self.xml_element_end),
                ('end', 'issueBackground', self.xml_element_end),
                ('end', 'remediationBackground', self.xml_element_end),
                ('end', 'issueDetail', self.xml_element_end),
                ('end', 'remediationDetail', self.xml_element_end),
                ),
            self.S_REQUESTRESPONSE_XML_ELEMENT : (
                ('end', 'request', self.xml_element_end_base64),
                ('end', 'response', self.xml_element_end_base64),
                ('end', 'responseRedirected', self.xml_element_end),
                ),
            }
        self.default_values = (
                ('serialNumber', ''),
                ('type', ''),
                ('name', ''),
                ('host', ''),
                ('hostip', ''),
                ('path', ''),
                ('location', ''),
                ('severity', ''),
                ('confidence', ''),
                ('issueBackground', ''),
                ('remediationBackground', ''),
                ('issueDetail', ''),
                ('remediationDetail', ''),
                ('request', b''),
                ('response', b''),
                ('responseRedirected', ''),
            )

        self.notes_values = ('name', 'severity', 'confidence', 'issueBackground', 'remediationBackground', 'issueDetail', 'remediationDetail')

    def make_results(self):
        cur = self.current

        host = cur['host']
        clean_host = self.re_clean_host.sub('', host)
        hostip = cur['hostip']
        url_path = cur['path'] or cur['location']
        url = urlparse.urljoin(host, url_path)
        request = self.util.split_request_block(cur['request'])
        response = self.util.split_response_block(cur['response'])

        method, req_url  = self.util.parse_method_url(request)
        method = str(method, 'ascii', 'ignore')
        if req_url:
            url_path = str(req_url, 'utf-8', 'ignore')
            url = urlparse.urljoin(host, url_path)
        status, content_type, datetime = self.util.parse_status_content_type_datetime(response)
        try:
            status = int(str(status, 'ascii', 'ignore'))
        except ValueError:
            pass
        except TypeError:
            pass
        content_type = str(content_type, 'utf-8', 'ignore')
        datetime = str(datetime, 'utf-8', 'ignore')

        # TODO: integrate vuln info
        notes_io = StringIO()
        for note_item in self.notes_values:
            if cur[note_item]:
                notes_io.write('%s: %s\n\n' % (note_item, cur[note_item]))
        
        return ('VULNXML', clean_host, hostip, url, status, datetime, request, response, method, content_type, {'notes':notes_io.getvalue()})

    def issues_start(self, elem):
        self.root = elem
        self.states.append(self.S_ISSUES)

    def issues_end(self, elem):
        raise(StopIteration)

    def issue_start(self, elem):
        self.current = {}
        for n, v in self.default_values:
            self.current[n] = v
        self.states.append(self.S_ISSUE)

    def issue_end(self, elem):
        elem.clear()
        self.states.pop()
        return self.make_results()

    def issue_xml_element_start(self, elem):
        self.states.append(self.S_ISSUE_XML_ELEMENT)

    def issue_host_start(self, elem):
        self.states.append(self.S_ISSUE_XML_ELEMENT)
        if elem.attrib.has_key('ip'):
            self.current['hostip'] = elem.attrib['ip']

    def requestresponse_start(self, elem):
        self.states.append(self.S_REQUESTRESPONSE)

    def requestresponse_end(self, elem):
        self.states.pop()
        
    def requestresponse_xml_element_start(self, elem):
        self.states.append(self.S_REQUESTRESPONSE_XML_ELEMENT)

    def xml_element_end(self, elem):
        if elem.text is None:
            self.current[elem.tag] = ''
        else:
            self.current[elem.tag] = self.re_encoded.sub(self.decode_entity, elem.text)
        self.states.pop()

    def xml_element_end_base64(self, elem):
        if elem.text is None:
            self.current[elem.tag] = b''
        elif 'base64' in elem.attrib and 'true' == elem.attrib['base64']:
            self.current[elem.tag] = base64.b64decode(elem.text)
        else:
            self.current[elem.tag] = bytes(self.re_encoded.sub(self.decode_entity, elem.text), 'utf-8') # TODO: or ascii?
        self.states.pop()

    def __iter__(self):
        return self

    def __next__(self):
        event, elem, tag, state = None, None, None, None
        while True:
            try:
                event, elem = next(self.iterator)
                tag = elem.tag
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
                print(('***%s***\n^^^%s^^^' % (self.source.last_response, self.source.buffer)))
                self.source.close()
                raise Exception('Internal error: state=%s, event=%s, elem=%s\n%s' % (state, event, elem.tag, traceback.format_exc()))

if '__main__' == __name__:
    # test code

    def process_file(mode, burpfile):
        if 'log' == mode:
            count = 0
            for result in burp_parse_log(burpfile):
                print(result)
                count += 1
            print(('processed %d records' % (count)))
        elif 'state' == mode:
            count = 0
            for result in burp_parse_state(burpfile):
                count += 1
            print(('processed %d records' % (count)))
        elif 'xml' == mode:
            count = 0
            for result in burp_parse_xml(burpfile):
                print(result)
                count += 1
            print(('processed %d records' % (count)))
        elif 'vulnxml' == mode:
            count = 0
            for result in burp_parse_vuln_xml(burpfile):
                print(result)
                count += 1
            print('processed %d records' % (count))
        elif 'dumpstate' == mode:
            for result in burp_dump_state(burpfile):
                print(result)
        else:
            raise Exception('unsupported mode: ' + mode)

    import sys
    if (len(sys.argv) != 3):
        sys.stderr.write('usage: %s [log|state|dumpstate|xml|vulnxml] [file]\n' % sys.argv[0])
        sys.exit(1)
    mode = sys.argv[1]
    infile = sys.argv[2]

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if infile.endswith('.zip'):
        zfile = zipfile.ZipFile(infile, 'r')
        for zi in zfile.infolist():
            process_file(mode, zfile.open(zi.filename, 'r'))
    else:
        process_file(mode, infile)



