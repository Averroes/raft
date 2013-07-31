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
# Classes to support parsing WebScarab converstation log files
import re, time, os
from urllib import parse as urlparse
import logging

class webscarab_parse_conversation():
    """ Parses Web Scarab conversation log file into request and result data """

    S_INITIAL = 0
    S_BEGIN_CONVERSATION = 1
    S_END_CONVERSATION = 2

    def __init__(self, wsfile):
        if 'conversationlog' != os.path.basename(wsfile) and os.path.isdir(wsfile):
            self.wsdir = wsfile
            wsfile = os.path.join(wsfile, 'conversationlog')
        else:
            self.wsdir = os.path.dirname(wsfile)
        self.convdir = os.path.join(self.wsdir, 'conversations')

        self.re_conversation = re.compile(br'^###\s+Conversation\s+:\s+(\d+)\s*$')
        self.re_data = re.compile(br'^(COMMENTS|WHEN|METHOD|COOKIE|STATUS|URL|ORIGIN|SET-COOKIE|SCRIPTS):\s+(.*)$')
        self.re_content_type = re.compile(br'^Content-Type:\s*([-_+0-9a-z.]+/[-_+0-9a-z.]+(?:\s*;\s*\S+=\S+)*)\s*$', re.I)

        self.logger = logging.getLogger(__name__)
        self.logger.info('Processing WebScarab conversation log file: %s' % (wsfile))
        self.wsfile = wsfile

        self.file = open(self.wsfile, 'rb')
        self.state = self.S_INITIAL

    def __iter__(self):
        return self

    def __read_line(self):
        line = self.file.readline()
        if not line:
            self.file.close()
            raise(StopIteration)
        return line

    def __process_file(self, filename):
        rfile = open(filename, 'rb')
        headers = ''
        body = ''
        data = rfile.read()
        n = data.find(b'\r\n\r\n')
        if -1 != n:
            # found headers
            headers = data[0:n+4]
            body = data[n+4:]
        else:
            n = data.find(b'\n\n')
            if -1 != n:
                # found headers
                headers = data[0:n+2]
                body = data[n+2:]
            else:
                self.logger.warn('failed to find end of headers: %s' % (filename))
                return (headers, body)

        return (headers, body)

    def __read_request(self, conversation):
        filename = os.path.join(self.convdir, '%s-request' % (conversation))
        if not os.path.isfile(filename):
            return None
        return self.__process_file(filename)

    def __read_response(self, conversation):
        filename = os.path.join(self.convdir, '%s-response' % (conversation))
        if not os.path.isfile(filename):
            return None
        return self.__process_file(filename)

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

    def __determine_content_type(self, headers):
        for header in headers.splitlines():
            m = self.re_content_type.search(header)
            if m:
                return m.group(1)
        return b''

    def __next__(self):
        while True:
            line = self.__read_line().rstrip()
            if self.state in (self.S_INITIAL, self.S_END_CONVERSATION):
                m = self.re_conversation.search(line)
                if m:
                    conversation = m.group(1)
                    self.state = self.S_BEGIN_CONVERSATION
                    method = b''
                    status = 0
                    url = b''
                    origin = b''
                    host = b''
                    hostip = b''
                    datetime = b''
                    content_type = b''
                    request, response = None, None
                else:
                    self.logger.debug('Leading garbage: %s' % (repr(line.decode('ascii','ignore'))))
            elif self.S_BEGIN_CONVERSATION == self.state:
                if 0 == len(line):
                    self.state = self.S_END_CONVERSATION
                    # return request/response
                    if request and response:
                        content_type = self.__determine_content_type(response[0])
                        return (origin.decode('utf-8','ignore'), host.decode('utf-8','ignore'), hostip.decode('utf-8','ignore'), url.decode('utf-8','ignore'), status, datetime.decode('utf-8','ignore'), request, response, method.decode('utf-8','ignore'), content_type.decode('utf-8','ignore'), {})
                    conversation = None
                else:
                    m = self.re_data.search(line)
                    if m:
                        name = m.group(1)
                        value = m.group(2)
                        if name in (b'COMMENTS', b'COOKIE',b'SET-COOKIE',b'SCRIPTS'):
                            # TODO: implement
                            pass
                        elif b'WHEN' == name:
                            datetime = bytes(time.asctime(time.localtime(int(value.decode('ascii','ignore'))/1000.0)),'ascii')
                        elif b'METHOD' == name:
                            method = value
                        elif b'STATUS' == name:
                            status = int(value[0:value.index(b' ')].decode('ascii','ignore'))
                            response = self.__read_response(conversation.decode())
                        elif b'URL' == name:
                            url, host = self.__normalize_url(value)
                            request = self.__read_request(conversation.decode())
                        elif b'ORIGIN' == name:
                            origin = value
                        else:
                            self.logger.debug('Unhandled data: [%s]=[%s]' % (repr(name.decode('ascii','ignore')), repr(value.decode('ascii','ignore'))))
                    else:
                        self.logger.debug('Garbage: %s' % (repr(line.decode('ascii','ignore'))))
            else:
                raise Exception

if '__main__' == __name__:
    # test code
    import sys
    if (len(sys.argv) != 3):
        sys.stderr.write('usage: %s [log] [file]\n' % sys.argv[0])
        sys.exit(1)
    mode = sys.argv[1]
    wsfile = sys.argv[2]

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if 'log' == mode:
        count = 0
        for result in webscarab_parse_conversation(wsfile):
            print(result)
            count += 1
        print(('processed %d records' % (count)))
    else:
        raise Exception

