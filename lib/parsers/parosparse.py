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
# Classes to support parsing Paros converstation log files
import re, time, os
from urllib import parse as urlparse
import logging

class paros_parse_message():
    """ Parses Web Scarab message log file into request and result data """

    def __init__(self, parosfile):

        self.re_message = re.compile(br'^==== (\d+) ==========\s*$')
        # XXX: copied from burp log parse, should refactor
        self.re_request = re.compile(br'^(\S+)\s+((?:https?://(?:\S+\.)+\w+(?::\d+)?)?/.*)\s+HTTP/\d+\.\d+\s*$')
        self.re_response = re.compile(br'^HTTP/\d+\.\d+\s+(\d{3}).*\s*$')
        self.re_content_length = re.compile(br'^Content-Length:\s*(\d+)\s*$', re.I)
        self.re_chunked = re.compile(br'^Transfer-Encoding:\s*chunked\s*$', re.I)
        self.re_date = re.compile(br'^Date:\s*(\w+,.*\w+)\s*$', re.I)
        self.re_content_type = re.compile(br'^Content-Type:\s*([-_+0-9a-z.]+/[-_+0-9a-z.]+(?:\s*;\s*\S+=\S+)*)\s*$', re.I)

        self.logger = logging.getLogger(__name__)
        self.logger.info('Processing Paros message log file: %s' % (parosfile))
        self.parosfile = parosfile

        self.file = open(self.parosfile, 'rb')

    def __iter__(self):
        return self

    def __normalize_url(self, url):
        parsed = urlparse.urlsplit(url)

        scheme = parsed.scheme
        netloc = parsed.netloc
        host = parsed.hostname

        # TODO: maybe change this to use hostname and port?
        if b'http' == scheme:
            netloc = netloc.replace(b':80',b'')
        elif b'https' == scheme:
            netloc = netloc.replace(b':443',b'')
        
        url = scheme + b'://' + netloc + parsed.path
        if parsed.query:
            url += b'?' + parsed.query
        if parsed.fragment:
            url += b'#' + parsed.fragment

        return (url, host)

    def __fixup_datetime(self, datetime):
        if datetime:
            try:
                tm = time.strptime(str(datetime,'ascii'), '%a, %d %b %Y %H:%M:%S %Z')
                tm = time.localtime(time.mktime(tm)-time.timezone)
                return bytes(time.asctime(tm),'ascii')
            except Exception as e:
                self.logger.debug('Failed parsing datetime [%s]: %s' % (datetime, e))
                return b''
        else:
            return b''
        
    def __process_buf(self, buf):
        method = b''
        status = 0
        url = b''
        origin = 'PROXY'
        host = b''
        hostip = b''
        datetime = b''
        content_type = b''
        request, response = None, None

        request_buf = []
        response_buf = []
        have_request, have_response = False, False
        request_offset, response_offset = 0, 0

        for line in buf:
            if have_response:
                response_buf.append(line)
                m = self.re_date.search(line)
                if m:
                    datetime = self.__fixup_datetime(m.group(1))
                else:
                    m = self.re_content_type.search(line)
                    if m:
                        content_type = m.group(1)
                if 0 == response_offset and 0 == len(line.rstrip()):
                    response_offset = len(response_buf)
            elif not have_request:
                m = self.re_request.search(line)
                if m:
                    method = m.group(1)
                    requrl = m.group(2)
                    url, host = self.__normalize_url(requrl)
                    request_buf.append(line)
                    have_request = True
            else:
                m = self.re_response.search(line)
                if m:
                    status = m.group(1)
                    response_buf.append(line)
                    have_response = True
                else:
                    request_buf.append(line)
                    if 0 == request_offset and 0 == len(line.rstrip()):
                        request_offset = len(request_buf)

        if len(request_buf) > 0:
            request_header = b''.join(request_buf[0:request_offset])
            request_body = b''.join(request_buf[request_offset:])
            if 0 == len(request_body.rstrip()):
                request_body = b''
            request = (request_header, request_body)
        if len(response_buf) > 0:
            response_header = b''.join(response_buf[0:response_offset])
            response_body = b''.join(response_buf[response_offset:])
            if 0 == len(response_body.rstrip()):
                response_body = b''
            response = (response_header, response_body)

        if bytes == type(status):
            status = int(status.decode('ascii','ignore'))

        return (origin, host.decode('utf-8','ignore'), hostip.decode('utf-8','ignore'), url.decode('utf-8','ignore'), status, datetime.decode('utf-8','ignore'), request, response, method.decode('utf-8','ignore'), content_type.decode('utf-8','ignore'), {})

    def __next__(self):
        have_http_request, have_http_response = False, False
        buf = []
        while True:
            line = self.file.readline()
            if not line:
                break

            m = self.re_message.search(line)
            if m:
                if len(buf) > 0:
                    return self.__process_buf(buf)
                buf = []
            else:
                buf.append(line)

        if len(buf) > 0:
            return self.__process_buf(buf)

        self.logger.debug('reached end of file')
        self.file.close()
        raise(StopIteration)

                
if '__main__' == __name__:
    # test code
    import sys
    if (len(sys.argv) != 3):
        sys.stderr.write('usage: %s [message] [file]\n' % sys.argv[0])
        sys.exit(1)
    mode = sys.argv[1]
    parosfile = sys.argv[2]

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if 'message' == mode:
        count = 0
        for result in paros_parse_message(parosfile):
            print(result)
            count += 1
        print(('processed %d records' % (count)))
    else:
        raise Exception

