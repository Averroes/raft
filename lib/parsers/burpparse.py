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
# Classes to support parsing Burp logs and state files
import re, time, struct
from urllib2 import urlparse
import zipfile, string
import logging, traceback

class BurpUtil():
    def __init__(self):
        self.re_content_type = re.compile(r'^Content-Type:\s*([-_+0-9a-z.]+/[-_+0-9a-z.]+(?:\s*;\s*\S+=\S+)*)\s*$', re.I)
        self.re_request = re.compile(r'^(\S+)\s+((?:https?://(?:\S+\.)+\w+(?::\d+)?)?/.*)\s+HTTP/\d+\.\d+\s*$', re.I)
        self.re_response = re.compile(r'^HTTP/\d+\.\d+\s+(\d{3}).*\s*$', re.M)

    def split_request_block(self, request):
        request_headers, request_body = self.split_block(request)
        return (request_headers, request_body)

    def split_response_block(self, response):
        response_headers, response_body = self.split_block(response)
        m = self.re_response.match(response_headers)
        if m and '100' == m.group(1):
            # TODO: decide if this is best way to handle
            actual_response_headers, actual_response_body = self.split_block(response_body)
            m = self.re_response.match(actual_response_headers)
            if m:
                return (response_headers + actual_response_headers, actual_response_body)
        return (response_headers, response_body)

    def split_block(self, block):
        c = 4
        n = block.find('\r\n\r\n')
        if -1 == n:
            c = 2
            block.find('\n\n')
        if -1 == n:
            n = len(block)
            c = 0
        return (block[0:n+c], block[n+c:])

    def get_content_type(self, headers):
        content_type = ''
        for line in headers.splitlines():
            m = self.re_content_type.search(line)
            if m:
                content_type = m.group(1)
                break
        return content_type

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
    T_TAG = 256

    def __init__(self, burpfile):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Parsing Burp state file: %s' % (burpfile))
        self.util = BurpUtil()
        self.burpfile = burpfile

        self.zfile = zipfile.ZipFile(burpfile, 'r')
        for zi in self.zfile.infolist():
            if zi.filename == 'burp':
                self.file = self.zfile.open(zi.filename, 'r')
                break
        else:
            raise(Exception('Failed to find valid entry: %s' % (burpfile)))

        self.states = []
        self.buffer = ''
        self.state = self.S_INITIAL

    def __iter__(self):
        return self

    def __read_data(self, length):

        data = ''
        if self.buffer:
            # buffered data
            if len(self.buffer) >= length:
                data = self.buffer[0:length]
                self.buffer = self.buffer[length:]
            else:
                data = self.buffer
                self.buffer = ''

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
            if '>' == b:
                break
        return data

    def read_next(self):
        return self.__read_next()

    def __read_next(self):
        token = self.__read_data(1)
        if '<' == token:
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
            else:
                raise(Exception('unhandled datatype: %d (%s)' % (datatype, token)))

    def __read_tag(self, tagname = None):
        result = self.__read_next()
        if tagname:
            if self.T_TAG != result[0] or tagname != result[1]:
                self.logger.error('failed on tag read; read: [%d,%s], expected: [%s]' % (result, tagname))
                raise(Exception('internal parse error'))
        else:
            if self.T_TAG != result[0]:
                self.logger.error('failed on tag read; read: [%d,%s]' % (result))
                raise(Exception('internal parse error'))
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
        self.__read_tag('<'+tagname+'>')
        result = self.__read_int()
        self.__read_tag('</'+tagname+'>')
        return result
        
    def __process_version(self):
        version = self.__read_node_int('version')
        self.logger.debug('read burp state version: %d', version)

    def __make_url(self, scheme, host, port, path):
        url = scheme + '://' + host
        if 'http' == scheme and 80 == port:
            pass
        elif 'https' == scheme and 443 == port:
            pass
        else:
            url += ':' + str(port)
        if '/' != path[0]:
            url += '/'
        url += path
        return url

    def __process_url(self):
        port = 80
        https = False
        scheme = 'http'
        path = None
        url = ''
        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and '</url>' == nextdata[1]):
            if self.T_TAG == nextdata[0]:
                tagname = nextdata[1]
                if '<https>' == tagname:
                    https = self.__read_bool()
                    if https:
                        scheme = 'https'
                    self.__read_tag('</https>')
                elif '<host>' == tagname:
                    host = self.__read_string()
                    self.__read_tag('</host>')
                elif '<file>' == tagname:
                    path = self.__read_string()
                    self.__read_tag('</file>')
                elif '<port>' == tagname:
                    port = self.__read_int()
                    self.__read_tag('</port>')
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
        method = ''
        content_type = ''

        # get method from request header
        headers = request[0]
        n = headers.find('\n')
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
        hostip = ''
        status = 0
        datetime = ''
        request = None
        response = None
        resplen = -1
        state = None

        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and '</info>' == nextdata[1]):
            if self.T_TAG == nextdata[0]:
                tagname = nextdata[1]
                if '<statusCode>' == tagname:
                    status = self.__read_int()
                    self.__read_tag('</statusCode>')
                elif '<responseLength>' == tagname:
                    resplen = self.__read_int()
                    self.__read_tag('</responseLength>')
                elif '<responseLength>' == tagname:
                    resplen = self.__read_int()
                    self.__read_tag('</responseLength>')
                elif '<response>' == tagname:
                    response = self.util.split_response_block(self.__read_string())
                    self.__read_tag('</response>')
                elif '<request>' == tagname:
                    request = self.util.split_request_block(self.__read_string())
                    self.__read_tag('</request>')
                elif '<state>' == tagname:
                    state = self.__read_int()
                    self.__read_tag('</state>')
                elif  '<time>' == tagname:
                    datetime = self.__read_datetime()
                    self.__read_tag('</time>')
                else:
                    self.logger.debug('unhandled tag: [%s]' % tagname)
            else:
                self.logger.debug('unhandled value: [%s]' % nextdata[1])

            nextdata = self.__read_next()

        if not request:
            return None

        method, content_type = self.__parse_method_content_type(request, response)
        return ('TARGET', host, hostip, url, status, datetime, request, response, method, content_type, {})
        
    def __process_item(self):
        nextdata = self.__read_next()
        result = None
        url = None
        host = None
        while not (self.T_TAG == nextdata[0] and '</item>' == nextdata[1]):
            if (self.T_TAG == nextdata[0] and '<url>' == nextdata[1]):
                url, host = self.__process_url()
            elif (self.T_TAG == nextdata[0] and '<info>' == nextdata[1]):
                if result:
                    raise(Exception('internal error; already have result'))
                result = self.__process_info(url, host)
            nextdata = self.__read_next()
        return result

    def __process_historyItem(self):

        hostip = ''
        host = ''
        status = 0
        datetime = ''
        request = None
        response = None
        resplen = -1

        url = None

        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and '</historyItem>' == nextdata[1]):
            if self.T_TAG == nextdata[0]:
                tagname = nextdata[1]
                if '<url>' == tagname:
                    url, host = self.__process_url()
                elif '<statusCode>' == tagname:
                    status = self.__read_int()
                    self.__read_tag('</statusCode>')
                elif '<ipAddress>' == tagname:
                    hostip = self.__read_string()
                    self.__read_tag('</ipAddress>')
                elif  '<time>' == tagname:
                    datetime = self.__read_datetime()
                    self.__read_tag('</time>')
                elif '<originalResponse>' == tagname:
                    response = self.util.split_response_block(self.__read_string())
                    self.__read_tag('</originalResponse>')
                elif '<originalRequest>' == tagname:
                    request = self.util.split_request_block(self.__read_string())
                    self.__read_tag('</originalRequest>')
                elif '<editedResponse>' == tagname:
                    response = self.util.split_response_block(self.__read_string())
                    self.__read_tag('</editedResponse>')
                elif '<editedRequest>' == tagname:
                    request = self.util.split_request_block(self.__read_string())
                    self.__read_tag('</editedRequest>')
                elif '<responseLength>' == tagname:
                    resplen = self.__read_int()
                    self.__read_tag('</responseLength>')
                else:
                    self.logger.debug('unhandled tag: [%s]' % tagname)
            else:
                self.logger.debug('unhandled value: [%s]' % nextdata[1])

            nextdata = self.__read_next()

        if not request:
            return None

        method, content_type = self.__parse_method_content_type(request, response)
        return ('PROXY', host, hostip, url, status, datetime, request, response, method, content_type, {})

    def __process_repeater_historyItem(self):

        hostip = ''
        host = ''
        status = 0
        datetime = ''
        request = None
        response = None
        resplen = -1

        url = None

        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and '</historyItem>' == nextdata[1]):
            if self.T_TAG == nextdata[0]:
                tagname = nextdata[1]
                if '<url>' == tagname:
                    url, host = self.__process_url()
                elif '<statusCode>' == tagname:
                    status = self.__read_int()
                    self.__read_tag('</statusCode>')
                elif '<ipAddress>' == tagname:
                    hostip = self.__read_string()
                    self.__read_tag('</ipAddress>')
                elif  '<time>' == tagname:
                    datetime = self.__read_datetime()
                    self.__read_tag('</time>')
                elif '<response>' == tagname:
                    response = self.util.split_response_block(self.__read_string())
                    self.__read_tag('</response>')
                elif '<request>' == tagname:
                    request = self.util.split_request_block(self.__read_string())
                    self.__read_tag('</request>')
                elif '<responseLength>' == tagname:
                    resplen = self.__read_int()
                    self.__read_tag('</responseLength>')
                else:
                    self.logger.debug('unhandled tag: [%s]' % tagname)
            else:
                self.logger.debug('unhandled value: [%s]' % nextdata[1])

            nextdata = self.__read_next()

        if not request:
            return None

        method, content_type = self.__parse_method_content_type(request, response)
        return ('REPEATER', host, hostip, url, status, datetime, request, response, method, content_type, {})

    def __process_requestPanel(self):
        nextdata = self.__read_next()
        result = None
        while not (self.T_TAG == nextdata[0] and '</requestPanel>' == nextdata[1]):
            if (self.T_TAG == nextdata[0] and '<historyItem>' == nextdata[1]):
                result = self.__process_repeater_historyItem()
            nextdata = self.__read_next()
        return result

    def __process_issue(self):

        hostip = ''
        host = ''
        status = 0
        datetime = ''
        request = None
        response = None
        notes = ''
        resplen = -1

        url = None

        # TODO: determine if better heuristic
        # issue can contain multiple response/request sets
        found_r = False

        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and '</issue>' == nextdata[1]):
            if self.T_TAG == nextdata[0]:
                tagname = nextdata[1]
                if found_r:
                    pass
                elif '<url>' == tagname:
                    url, host = self.__process_url()
                elif '<statusCode>' == tagname:
                    status = self.__read_int()
                    self.__read_tag('</statusCode>')
                elif '<ipAddress>' == tagname:
                    hostip = self.__read_string()
                    self.__read_tag('</ipAddress>')
                elif '<id>' == tagname:
                    notes = self.__read_string()
                    self.__read_tag('</id>')
                elif  '<time>' == tagname:
                    datetime = self.__read_datetime()
                    self.__read_tag('</time>')
                elif '<response>' == tagname:
                    response = self.util.split_response_block(self.__read_string())
                    self.__read_tag('</response>')
                elif '<request>' == tagname:
                    request = self.util.split_request_block(self.__read_string())
                    self.__read_tag('</request>')
                elif '<responseLength>' == tagname:
                    resplen = self.__read_int()
                    self.__read_tag('</responseLength>')
                elif '</r>' == tagname:
                    found_r = True
                else:
                    self.logger.debug('unhandled tag: [%s]' % tagname)
            else:
                self.logger.debug('unhandled value: [%s]' % nextdata[1])

            nextdata = self.__read_next()

        if not request:
            return None

        method, content_type = self.__parse_method_content_type(request, response)
        return ('SCANNER', host, hostip, url, status, datetime, request, response, method, content_type, {'notes':notes, 'confirmed':True}) # TODO: confirmed hard-coded

    def __process_hps(self):
        # ignore
        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and '</hps>' == nextdata[1]):
            nextdata = self.__read_next()
        return None

    def __read_until_tag(self, tagname):
        # ignore
        nextdata = self.__read_next()
        while not (self.T_TAG == nextdata[0] and tagname == nextdata[1]):
            nextdata = self.__read_next()

    def next(self):
        while True:
            if self.S_INITIAL == self.state:
                self.__process_version()
                self.state = self.S_VERSION
            elif self.state in (self.S_VERSION, self.S_END_STATE):
                nexttag = self.__read_tag()
                if '<config>' == nexttag:
                    self.state = self.S_BEGIN_CONFIG
                elif '<state>' == nexttag:
                    self.state = self.S_BEGIN_STATE
                else:
                    raise(Exception('internal state error; invalid transition from [%s] to [%s]' % (self.state, nexttag)))
            elif self.state in (self.S_BEGIN_STATE, self.S_END_TARGET, self.S_END_PROXY, self.S_END_SCANNER, self.S_END_REPEATER):
                nexttag = self.__read_tag()
                if '<target>' == nexttag:
                    self.state = self.S_BEGIN_TARGET
                elif '<proxy>' == nexttag:
                    self.state = self.S_BEGIN_PROXY
                elif '<scanner>' == nexttag:
                    self.state = self.S_BEGIN_SCANNER
                elif '<repeater>' == nexttag:
                    self.state = self.S_BEGIN_REPEATER
                elif '</state>' == nexttag:
                    self.state = self.S_END_STATE
                else:
                    raise(Exception('internal state error; invalid transition from [%s] to [%s]' % (self.state, nexttag)))
            elif self.S_BEGIN_TARGET == self.state:
                nexttag = self.__read_tag()
                if '<item>' == nexttag:
                    result = self.__process_item()
                    if result:
                        return result
                elif '</target>' == nexttag:
                    self.state = self.S_END_TARGET
                else:
                    raise(Exception('internal state error; invalid transition from [%s] to [%s]' % (self.state, nexttag)))
            elif self.S_BEGIN_PROXY == self.state:
                nexttag = self.__read_tag()
                if '<historyItem>' == nexttag:
                    result = self.__process_historyItem()
                    if result:
                        return result
                elif '</proxy>' == nexttag:
                    self.state = self.S_END_PROXY
                else:
                    raise(Exception('internal state error; invalid transition from [%s] to [%s]' % (self.state, nexttag)))
            elif self.S_BEGIN_SCANNER == self.state:
                nexttag = self.__read_tag()
                if '<issue>' == nexttag:
                    result = self.__process_issue()
                    if result:
                        return result
                elif '<paused>' == nexttag:
                    paused = self.__read_bool()
                    self.__read_tag('</paused>')
                elif '<hps>' == nexttag:
                    self.__process_hps()
                elif '<queueitem>' == nexttag:
                    self.__read_until_tag('</queueitem>')
                elif '<asi>' == nexttag:
                    self.__read_until_tag('</asi>')
                elif '<has>' == nexttag:
                    self.__read_until_tag('</has>')
                elif '</scanner>' == nexttag:
                    self.state = self.S_END_SCANNER
                else:
                    raise(Exception('internal state error; invalid transition from [%s] to [%s]' % (self.state, nexttag)))
            elif self.state in (self.S_BEGIN_REPEATER, self.S_END_REQUEST_PANEL):
                nexttag = self.__read_tag()
                if '<requestPanel>' == nexttag:
                    self.state = self.S_BEGIN_REQUEST_PANEL
                elif '</repeater>' == nexttag:
                    self.state = self.S_END_REPEATER
                else:
                    raise(Exception('internal state error; invalid transition from [%s] to [%s]' % (self.state, nexttag)))
            elif self.S_BEGIN_REQUEST_PANEL == self.state:
                nexttag = self.__read_tag()
                if '<tabCaption>' == nexttag:
                    self.__read_until_tag('</tabCaption>')
                elif '<historyIndex>' == nexttag:
                    self.__read_until_tag('</historyIndex>')
                elif '<displayedService>' == nexttag:
                    self.__read_until_tag('</displayedService>')
                elif '<displayedRequest>' == nexttag:
                    self.__read_until_tag('</displayedRequest>')
                elif '<historyItem>' == nexttag:
                    result = self.__process_repeater_historyItem()
                    if result:
                        return result
                elif '</requestPanel>' == nexttag:
                    self.state = self.S_END_REQUEST_PANEL
                else:
                    raise(Exception('internal state error; invalid transition from [%s] to [%s]' % (self.state, nexttag)))
            elif self.S_BEGIN_CONFIG == self.state:
                self.__read_until_tag('</config>')
                self.state = self.S_END_CONFIG
            elif self.S_END_CONFIG == self.state:
                self.logger.debug('reached end configuration state')
                self.file.close()
                raise(StopIteration)
            else:
                raise(Exception('unhandled state: %s' % (self.state)))

class burp_dump_state(burp_parse_state):
    """ For exploration of state content """

    def next(self):
        return burp_parse_state.read_next(self)

class burp_parse_log():
    """ Parses Burp log file into request and result data """

    DELIMITER = '======================================================'

    S_INITIAL = 1
    S_DELIMITER = 2
    S_BURP_HEADER = 3
    S_HTTP_REQUEST = 4
    S_HTTP_RESPONSE = 5

    def __init__(self, burpfile):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Parsing Burp log file: %s' % (burpfile))
        self.util = BurpUtil()
        self.burpfile = burpfile

        self.re_burp = re.compile(r'^(\d{1,2}:\d{1,2}:\d{1,2}\s+(?:AM|PM))\s+(https?://(?:\S+\.)*\w+:\d+)(?:\s+\[((?:\d{1,3}\.){3}\d{1,3})\])?\s*$', re.I)
        self.re_content_length = re.compile(r'^Content-Length:\s*(\d+)\s*$', re.I)
        self.re_chunked = re.compile(r'^Transfer-Encoding:\s*chunked\s*$', re.I)
        self.re_chunked_length = re.compile('^[a-f0-9]+$', re.I)
        self.re_date = re.compile(r'^Date:\s*(\w+,.*\w+)\s*$', re.I)

        self.file = open(self.burpfile, 'rb')

        self.state = self.S_INITIAL
        self.peaked = False
        self.peakbuf = ''

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
        if 'http' == scheme:
            netloc = netloc.replace(':80','')
        elif 'https' == scheme:
            netloc = netloc.replace(':443','')
        
        url = scheme + '://' + netloc + p2.path
        if p2.query:
            url += '?' + p2.query
        if p2.fragment:
            url += '#' + p2.fragment

        return url, host

    def __synthesize_date(self, burptime, datetime):
        if not burptime and not datetime:
            return ''
        if datetime:
            try:
                tm = time.strptime(datetime, '%a, %d %b %Y %H:%M:%S %Z')
                tm = time.localtime(time.mktime(tm)-time.timezone)
            except Exception, e:
                self.logger.debug('Failed parsing datetime [%s]: %s' % (datetime, e))
        else:
            tm = time.localtime()

        # use today's date
        # TODO: improve
        n = burptime.rfind(' ')
        hms = burptime[0:n].split(':')
        ampm = burptime[n+1:]

        h = int(hms[0])
        if 'PM' == ampm:
            if h < 12:
                h += 12
        elif 'AM' == ampm:
            if h == 12:
                h = 0

        m = int(hms[1])
        s = int(hms[2])
        if h > tm.tm_hour:
            # assume this was yesterday
            tm = time.localtime(time.mktime(tm)-60*60*24)

        reqtm = time.mktime((tm.tm_year, tm.tm_mon, tm.tm_mday, h, m, s, tm.tm_wday, tm.tm_yday, tm.tm_isdst))
        return time.asctime(time.localtime(reqtm))

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
            raise(Exception('Internal error: bad data read [%d] versus [%d]' % (len(data), length)))
        return data

    def __read_chunked(self, line):
        data = ''
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
        body = ''
        datetime = ''
        content_type = ''
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
        return self.__process_block(firstline, 'HEAD' == method.upper())
        
    def next(self):
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
                        hostip = parsed.netloc[0:parsed.netloc.find(':')]
                    have_burp_header = True
                    have_http_request, have_http_response = False, False
                    request, response = None, None
                    url = hosturl
                    datetime = ''
                    status = 0
                    method = ''
                    requrl = ''
                    content_type = ''
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
                        return ('LOG', host, hostip, url, status, datetime, request, response, method, content_type, {})
                else:
                    self.logger.debug('Garbage: %s' % (line))
            else:
                raise(Exception('unhandled state: %s' % (self.state)))

class burp_parse_xml():
    """ parse Burp broken XML format """

    S_INITIAL = 1
    S_ITEMS = 2
    S_ITEM = 3

    S_ITEM_XML_ELEMENT = 101

    class BurpBrokenXml(object):
        def __init__(self, filename):
            self.xmlfile = open(filename, 'rb')
            self.buffer = ''
            self.re_nonprintable = re.compile('[^%s]' % re.escape('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r'))
            self.entity_encode = lambda m: '&#x%02X;' % ord(m.group(0))
            self.name = '<BurpBrokenXml>'
            self.closed = False
            self.last_response = ''
            self.buffer = ''

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
                    self.buffer = ''
            else:
                fixed = self.re_nonprintable.sub(self.entity_encode, raw)
                if self.buffer:
                    response = self.buffer + fixed
                    self.buffer = ''
                else:
                    response = fixed
            if -1 != size and response:
                rlen = len(response)
                if rlen > size:
                    # TODO: avoid splitting encoded entities across buffers ?
                    apos = response.rfind('&', size - 6, size)
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

        self.burpfile = burpfile
        self.re_encoded = re.compile(r'&#[xX]([0-9a-fA-F]{2});')
        self.decode_entity = lambda m: '%c' % (int(m.group(1),16))

        self.source = burp_parse_xml.BurpBrokenXml(self.burpfile)

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
        url = cur['url']
        datetime = cur['time']
        method = cur['method']
        request = self.util.split_request_block(cur['request'])
        response = self.util.split_response_block(cur['response'])
        if response and response[0]:
            content_type = self.util.get_content_type(response[0])
        else:
            content_type = ''

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
        if elem.attrib.has_key('ip'):
            self.current['hostip'] = elem.attrib['ip']

    def xml_element_end(self, elem):
        self.current[elem.tag] = self.re_encoded.sub(self.decode_entity, str(elem.text))
        self.states.pop()

    def xml_element_end_base64(self, elem):
        if elem.attrib.has_key('base64') and 'true' == elem.attrib['base64']:
            self.current[elem.tag] = str(elem.text).decode('base64')
        else:
            self.current[elem.tag] = self.re_encoded.sub(self.decode_entity, str(elem.text))
        self.states.pop()
            
    def __iter__(self):
        return self

    def next(self):
        event, elem, tag, state = None, None, None, None
        while True:
            try:
                event, elem = self.iterator.next()
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
                print('***%s***\n^^^%s^^^' % (self.source.last_response, self.source.buffer))
                self.source.close()
                raise Exception('Internal error: state=%s, event=%s, elem=%s\n%s' % (state, event, elem.tag, traceback.format_exc(error)))

if '__main__' == __name__:
    # test code
    import sys
    if (len(sys.argv) != 3):
        sys.stderr.write('usage: %s [log|state|dumpstate] [file]\n' % sys.argv[0])
        sys.exit(1)
    mode = sys.argv[1]
    burpfile = sys.argv[2]

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if 'log' == mode:
        count = 0
        for result in burp_parse_log(burpfile):
            print(result)
            count += 1
        print('processed %d records' % (count))
    elif 'state' == mode:
        count = 0
        for result in burp_parse_state(burpfile):
            count += 1
        print('processed %d records' % (count))
    elif 'xml' == mode:
        count = 0
        for result in burp_parse_xml(burpfile):
            print(result)
            count += 1
        print('processed %d records' % (count))
    elif 'dumpstate' == mode:
        for result in burp_dump_state(burpfile):
            print(result)
    else:
        raise(Exception('unsupported mode: %s' % (mode)))

