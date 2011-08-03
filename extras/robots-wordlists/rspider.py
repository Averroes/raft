#!/usr/bin/env python
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

import zipfile, bz2, gzip, zlib
import sys, time
import socket, select, struct, errno
import re
import string
import collections
import argparse
from cStringIO import StringIO
from xml.sax.saxutils import escape
from urllib2 import urlparse
import traceback
import adns
from OpenSSL import SSL

class Client:

    NOLINGER = struct.pack('ii', 1, 0)

    S_DISCONNECTED = 0
    S_CONNECTED = 1
    S_REQUEST_SENT = 2
    S_RESPONSE_READ = 3
    S_NEED_SSL_HANDSHAKE = 4
    S_SSL_WANT_READ = 5
    S_SSL_WANT_WRITE = 6

    MAX_CONTENT_SIZE = 2000000

    re_nonprintable = re.compile('[^%s]' % re.escape('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r'))
    re_status_line = re.compile(r'^HTTP/\d\.\d\s+\d{3}(?:\s+.*)?$')
    re_ipaddr = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

    def __init__(self, method, useragent, append_headers, quiet):
        self.csock = None
        self.tsock = None
        self.method = method
        self.useragent = useragent
        self.append_headers = append_headers
        self.quiet = quiet
        self.state = self.S_DISCONNECTED
        self.use_ssl = False
        self.reset_values()

    def reset_values(self):
        self.request = None
        self.response_io = None
        self.start_time = 0
        self.connect_time = 0
        self.ip_address = ''
        self.port = 0
        self.url = ''
        self.host = ''

    def do_encode(self, text):
        if self.re_nonprintable.search(text):
            return True
        return False

    def connect(self, ip_address, port, is_ssl):
        ok = False
        try:
            self.reset_values()
            self.connect_time = time.time()
            self.tsock = None
            self.use_ssl = is_ssl
            if self.use_ssl:
                self.context = SSL.Context(SSL.SSLv23_METHOD)
            self.csock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.csock.setblocking(0)
            self.csock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, self.NOLINGER)
            self.csock.connect((ip_address, port))
            ok = True
        except socket.error, e:
            if e.errno == errno.EINPROGRESS:
                ok = True
            else:
                if not self.quiet:
                    sys.stderr.write('failed on connect [%s:%d]: %s\n' % (ip_address, port, e))
        if ok:
            self.ip_address = ip_address
            self.port = port
            if self.use_ssl:
                self.state = self.S_NEED_SSL_HANDSHAKE
            else:
                self.state = self.S_CONNECTED

        return ok

    def close(self):
        try:
            if self.csock:
                if self.use_ssl and not self.state == self.S_NEED_SSL_HANDSHAKE:
                    ok = self.csock.shutdown()
                self.csock.close()
                self.csock = None
        except socket.error, e:
            if not self.quiet:
                sys.stderr.write('failed on close: %s\n' % (e))

        self.state = self.S_DISCONNECTED

    def is_connected(self):
        return self.csock and self.state != self.S_DISCONNECTED

    def is_open(self):
        return self.csock and self.state in (self.S_RESPONSE_READ,)

    def is_readable(self):
        return self.csock and self.state in (self.S_REQUEST_SENT, self.S_NEED_SSL_HANDSHAKE, self.S_SSL_WANT_READ)

    def is_writeable(self):
        return self.csock and self.state in (self.S_CONNECTED, self.S_RESPONSE_READ, self.S_NEED_SSL_HANDSHAKE, self.S_SSL_WANT_WRITE)

    def need_ssl_handshake(self):
        return self.use_ssl and self.csock and self.state in (self.S_NEED_SSL_HANDSHAKE, self.S_SSL_WANT_READ, self.S_SSL_WANT_WRITE)

    def fileno(self):
        if self.state == self.S_DISCONNECTED or not self.csock:
            return -1
        return self.csock.fileno()

    def elapsed_seconds(self, now):
        if self.start_time:
            return now - self.start_time
        elif self.connect_time:
            return now - self.connect_time
        else:
            return 0

    def do_handshake(self):
        try:
            if not self.tsock:
                self.tsock = self.csock
                self.csock = SSL.Connection(self.context, self.tsock)
                self.csock.set_connect_state()
            self.csock.do_handshake()
            self.state = self.S_CONNECTED
        except SSL.Error, e:
            if type(e) == SSL.WantReadError:
                self.state = self.S_SSL_WANT_READ
            elif type(e) ==  SSL.WantWriteError:
                self.state = self.S_SSL_WANT_WRITE
            else:
                if not self.quiet:
                    sys.stderr.write('failed on do_handshake (socket) [%s]: %s\n' % (self.ip_address, e))
                self.close()
                return False
        except socket.error, e:
            if e.errno in (errno.EINPROGRESS, errno.EWOULDBLOCK):
                pass
            else:
                if not self.quiet:
                    sys.stderr.write('failed on do_handshake (socket) [%s]: %s\n' % (self.ip_address, e))
                self.close()
                return False

        return True

    def send_request(self, url):

        if not self.request:
            splitted = urlparse.urlsplit(url)
            host = splitted.hostname
            pathuri = path = splitted.path
            if splitted.query:
                pathuri += '?' + splitted.query

            self.start_time = time.time()
            self.url = url
            self.host = host
            self.path = path

            io = StringIO()
            io.write('%s %s HTTP/1.0\r\n' % (self.method, pathuri))
            if not self.re_ipaddr.match(host):
                io.write('Host: %s\r\n' % (host))
            io.write('User-Agent: %s\r\n' % (self.useragent))
            io.write('Accept-Encoding: gzip, deflate\r\n')
            io.write('Connection: close\r\n')
            if self.append_headers:
                io.write(self.append_headers)
            if False and -1 != self.MAX_CONTENT_SIZE:
                # TODO: send If-Range: ?
                # Some load-balancer servers seem to treat this as a HTTP/1.1 request
                io.write('Range: bytes=0-%d\r\n' % (self.MAX_CONTENT_SIZE-1))
            io.write('\r\n')
            self.request = io.getvalue()
            self.written = 0
            self.to_write = len(self.request)

        sent, ok = True, True
        try:
            data_written = self.csock.send(self.request[self.written:])
            self.written += data_written
            self.to_write -= data_written
            if self.to_write <= 0:
                self.state = self.S_REQUEST_SENT
            else:
                sent = False
        except SSL.Error, e:
#            print('SSL.Error: %s (%s)' % (e, type(e)))
            if type(e) in (SSL.WantReadError, SSL.WantWriteError):
                sent = False
            else:
                ok = False
                if not self.quiet:
                    sys.stderr.write('failed on send_request (SSL) [%s]: %s\n' % (self.host, e))
                self.close()
        except socket.error, e:
            if e.errno == errno.EAGAIN:
                sent = False
            else:
                ok = False
                if not self.quiet:
                    sys.stderr.write('failed on send_request [%s]: %s\n' % (self.host, e))
                self.close()

        return sent, ok

    def read_response(self, output):

        if not self.response_io:
            self.response_io = StringIO()

        finished = True
        try:
            while True:
                tmp = self.csock.recv(4096)
                if not tmp:
                    break
                self.response_io.write(tmp)
        except SSL.Error, e:
            if type(e) in (SSL.WantReadError, SSL.WantWriteError):
                finished = False
            elif type(e) == SSL.ZeroReturnError:
                # connection closed
                pass
            elif (-1, 'Unexpected EOF') == e.args:
                # some servers generate this
                pass
            else:
                if not self.quiet:
                    sys.stderr.write('failed on read_response (SSL) [%s]: %s\n' % (self.host, type(e)))
        except socket.error, e:
            if e.errno == errno.EAGAIN:
                finished = False
            else:
                if not self.quiet:
                    sys.stderr.write('warn: failed request [%s] %s\n' % (self.host, e))

        if not finished:
            return finished, None
            
        self.close()

        response = self.response_io.getvalue()
        self.response_io.close()
        self.response_io = None

        results = StringIO()

        results.write('<capture>\n')
        results.write('<request>\n')
        results.write('<method>%s</method>\n' % (self.method))
        results.write('<url>%s</url>\n' % escape(self.url))
        results.write('<host>%s</host>\n' % escape(self.host))
        results.write('<hostip>%s</hostip>\n' % escape(self.ip_address))
        results.write('<datetime>%s GMT</datetime>\n' % escape(time.asctime(time.gmtime(self.start_time))))

        if self.do_encode(self.request):
            results.write('<headers encoding="base64">')
            results.write(self.request.encode('base64'))
            results.write('</headers>\n')
        else:
            results.write('<headers>')
            results.write(escape(self.request))
        results.write('</headers>\n')
        results.write('<body></body>\n')
        results.write('</request>\n')

        redirect = None
        if response:
            headers = response
            body = ''
            version, status, reason = '', '', ''
            content_length = -1
            content_type = ''
            content_encoding = ''
            prev = 0
            broken_server_response = False
            while True:
                n = response.find('\n', prev)
                if -1 == n:
                    break
                if n > 0 and '\r' == response[n-1]:
                    line = response[prev:n-1]
                else:
                    line = response[prev:n]
                if 0 == len(line):
                    if broken_server_response or '100' == status:
                        prev = n + 1
                        continue
                    # end of headers
                    headers = response[0:n+1]
                    body = response[n+1:]
                    break

                if 0 == prev and line.count(' ') > 1:
                    version, status, reason = line.split(' ', 2)
                elif 0 == prev and 'close' == line:
                    # some broken servers just respond with 'close' as the first header
                    broken_server_response = True
                elif not status and self.re_status_line.search(line):
                    if line.count(' ') > 1:
                        version, status, reason = line.split(' ', 2)
                    else:
                        version, status = line.split(' ')
                elif line[0] in (' ', '\t'):
                    # continuation ?
                    pass
                elif not status and -1 != line.lower().find('<html'):
                    # HTTP/0.9 response
                    headers = ''
                    body = response[0:]
                    break
                elif ':' in line:
                    broken_server_response = False
                    name, value = line.split(':', 1)
                    value = value.strip()
                    lname = name.strip().lower()
                    if 'location' == lname:
                        redirect = value
                    elif 'content-length' == lname:
                        if value:
                            try:
                                content_length = int(value)
                            except ValueError:
                                pass
                    elif 'content-type' == lname:
                        content_type = value
                    elif 'content-encoding' == lname:
                        content_encoding = value

                prev = n + 1

            if len(body) > 0:
                try:
                    if 'gzip' == content_encoding:
                        rio = StringIO(body)
                        rio.seek(0,0)
                        gz = gzip.GzipFile(None, 'rb', None, rio)
                        body = gz.read()
                        gz.close()
                    elif content_encoding in ('deflate', 'compress'):
                        body = zlib.decompress(body, -15)
                    # store real length
                    content_length = len(body)
                except Exception, e:
                    if not self.quiet:
                        sys.stderr.write('warning: [%s] ignoring: %s\n' % (self.host, e))

            if -1 == content_length:
                content_length = len(body)

            if self.MAX_CONTENT_SIZE != -1 and len(body) > self.MAX_CONTENT_SIZE:
                body = body[0:self.MAX_CONTENT_SIZE]

            results.write('<response>\n')
            if status and not self.re_nonprintable.search(status):
                results.write('<status>%s</status>\n' % escape(status))
            if content_type and not self.re_nonprintable.search(content_type):
                results.write('<content_type>%s</content_type>\n' % escape(content_type))
            results.write('<content_length>%s</content_length>\n' % content_length)
            results.write('<elapsed>%d</elapsed>\n' % int((time.time() - self.start_time)*1000))
            
            if self.do_encode(headers):
                results.write('<headers encoding="base64">')
                results.write(headers.encode('base64'))
                results.write('</headers>\n')
            else:
                results.write('<headers>')
                results.write(escape(headers))
                results.write('</headers>\n')

            if self.do_encode(body):
                results.write('<body encoding="base64">')
                results.write(body.encode('base64'))
                results.write('</body>\n')
            else:
                results.write('<body>')
                results.write(escape(body))
                results.write('</body>\n')

            results.write('</response>\n')

        results.write('</capture>\n')
        output.write(results.getvalue())
        results.close()

        # TODO: this is ghetto to check for redirect request here
        if redirect:
            redirect = urlparse.urljoin(self.url, redirect)
            splitted = urlparse.urlsplit(redirect)
            if splitted.hostname and splitted.scheme in ('http','https') and (self.host.endswith(splitted.hostname) or splitted.hostname.endswith(self.host)):
                if not self.path in redirect or self.url == redirect:
                    redirect = None
            else:
                redirect = None

        return finished, redirect

class BatchedReader:

    def __init__(self, infile, callback, batch_count = 10, total_count = -1, skip_count = -1 ):
        self.infile = infile
        self.callback = callback
        self.batch_count = batch_count
        self.total_count = total_count
        self.skip_count = skip_count
        self.count = 0
        self.linecount = 0
        self.this_count = 0
        self.finished = False

    def __iter__(self):
        return self

    def next(self):
        if self.finished:
            if self.infile:
                self.infile.close()
                self.infile = None
            raise StopIteration
        try:
            while True:
                if self.this_count >= self.batch_count:
                    self.this_count = 0
                    raise StopIteration

                if self.total_count != -1 and self.count >= self.total_count:
                    self.finished = True
                    raise StopIteration

                line = self.infile.readline()
                if not line or 0 == len(line.rstrip()):
                    self.finished = True
                    raise StopIteration
                self.linecount += 1

                if self.skip_count == -1 or self.linecount > self.skip_count:
                    ret = apply(self.callback, (line,))
                    if ret:
                        self.count += 1
                        self.this_count += 1
                        return ret

        except StopIteration:
            raise
        except Exception, e:
            sys.stderr.write('oops: %s' % (traceback.format_exc(e)))
            raise StopIteration

class RSpider:

    def __init__(self, hostfile, total_count, skip_count, method, path, useragent, append_headers, noredirects, nossl, timeout, clients, quiet):

        self.hostfile = hostfile
        self.total_count = total_count
        self.skip_count = skip_count
        self.method = method
        self.path = path
        self.useragent = useragent
        self.append_headers = None
        if append_headers:
            self.append_headers = ''
            for header in append_headers:
                self.append_headers += header + '\r\n'
        self.noredirects = noredirects
        self.nossl = nossl
        self.timeout = timeout
        self.numclients = clients
        self.batch_count = self.numclients
        self.quiet = quiet

        self.re_ipaddr = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        self.cut_count = 10000

        self.resolver = adns.init(adns.iflags.noautosys) # TODO: what does this flag mean?
        self.pending_requests = {}
        self.queries = {}
        self.requests = collections.deque()
        self.recent_requests = []
        self.recent_requests_max = 101
        self.recent_requests_count = 0
        for i in range(0, self.recent_requests_max):
            self.recent_requests.append('')

        if hostfile.endswith('.zip'):
            zfile = zipfile.ZipFile(hostfile, 'r')
            zi = zfile.infolist()
            if 1 == len(zi):
                self.infile = zfile.open(zi[0], 'r')
            else:
                raise Exception('unable to determine file in zipfile')
        elif hostfile.endswith('.bz2'):
            self.infile = bz2.BZ2File(hostfile, 'r')
        else:
            self.infile = open(hostfile, 'r')

        self.request_generator = BatchedReader(self.infile, self.process_line, self.batch_count, self.total_count, self.skip_count)

        socket.setdefaulttimeout(max(5, self.timeout - 5))

        self.clients = []
        for i in range(0, self.numclients):
            self.clients.append(Client(self.method, self.useragent, self.append_headers, self.quiet))


    def process_line(self, line):
        line = line.rstrip()
        if not line:
            return None
        if not ',' in line:
            url = line
        else:
            fields = line.split(',')
            url = fields[1]
        host = url
        scheme = 'http'
        path = self.path
        if '/' in url:
            splitted = urlparse.urlsplit(url)
            if splitted.scheme:
                scheme = splitted.scheme
            if splitted.hostname:
                host = splitted.hostname
            if splitted.path:
                path = splitted.path
        url = urlparse.urlunsplit((scheme, host, path, '', ''))
        return url

    def open_results(self):
        self.results = bz2.BZ2File('results-%s.xml.bz2' % str(int(time.time()*1000)), 'w')
        self.results.write('<raft version="1.0">\n')

    def close_results(self):
        self.results.write('</raft>')
        self.results.close()

    def next_request(self):
        # first handle completed DNS
        for query in self.resolver.completed():
            host = self.queries.pop(query)
            if not self.pending_requests.has_key(host):
                if not self.quiet:
                    sys.stderr.write('warning: missing host [%s] in pending_requests\n' % (host))
                continue
            urls = self.pending_requests.pop(host)
            answer = query.check()
            if answer[0] or len(answer[3]) == 0:
                if 101 == answer[0] and answer[1] and host != answer[1]:
                    self.retry_with_cname(answer[1], urls)
                elif not host.startswith('www.'):
                    self.retry_with_www(host, urls)
                else:
                    if not self.quiet:
                        sys.stderr.write('failed to resolve host [%s]\n' % (host))
            else:
                for url in urls:
                    self.requests.appendleft((url, answer[3][0]))

        # return next resolved request
        if len(self.requests) == 0:
            return None
        return self.requests.pop()

    def retry_with_cname(self, cname, urls):
        sys.stdout.write('--->%s using %s (%d)\n' % (','.join(urls), cname, len(self.requests)))
        self.append_request(cname, urls)
        
    def retry_with_www(self, host, urls):
        if self.re_ipaddr.match(host):
            return
        wwwhost = 'www.'+host
        for url in urls:
            splitted = urlparse.urlsplit(url)
            newurl = urlparse.urlunsplit(('http', wwwhost, splitted.path, splitted.query, ''))
            self.add_request(newurl)

    def retry_with_https(self, host, url, ip_address):
        if self.nossl:
            return
        splitted = urlparse.urlsplit(url)
        newurl = urlparse.urlunsplit(('https', host, splitted.path, splitted.query, ''))
        self.add_resolved_request(newurl, ip_address)

    def add_resolved_request(self, url, ip_address):
        self.requests.appendleft((url, ip_address))

    def add_request(self, url):
        sys.stdout.write('--->%s (%d)\n' % (url, len(self.requests)))
        splitted = urlparse.urlsplit(url)
        host = splitted.hostname
        self.append_request(host, [url])

    def append_request(self, host, request_urls):
        urls = []
        for url in request_urls:
            if self.re_ipaddr.match(host):
                # already in IP address format
                self.add_resolved_request(url, host)
            else:
                request_key = '%s:%s' % (host, url)
                if request_key in self.recent_requests:
                    if not self.quiet:
                        sys.stderr.write('skipping %s on %s due to recent query\n' % (url, host))
                else:
                    urls.append(url)
                    self.recent_requests[self.recent_requests_count % self.recent_requests_max] = request_key
                    self.recent_requests_count += 1
        if len(urls) > 0:
            query = self.resolver.submit(host, adns.rr.A, 0)
            self.queries[query] = host
            if not self.pending_requests.has_key(host):
                self.pending_requests[host] = urls
            else:
                self.pending_requests[host].extend(urls)

    def outstanding_requests(self):
#        print(self.pending_requests, self.requests)
        return len(self.pending_requests) + len(self.requests)

    def get_url_port_info(self, url):
        splitted = urlparse.urlsplit(url)
        is_ssl = splitted.scheme == 'https'
        port = None
        try:
            if splitted.port:
                port = splitted.port
        except ValueError, e:
            if not self.quiet:
                sys.stderr.write('ignoring malformed url [%s]: %s\n' % (url, e))
        if not port:
            if is_ssl:
                port = 443
            else:
                port = 80

        return port, is_ssl

    def run_requests(self, generator):
        dispatch_list = {}
        inflight_list = {}
        retry_list = []
        redirect_list = {}
        url = ''
        rcount = 0
        wcount = 0
        while True:
            try:
                if self.outstanding_requests() < self.numclients:
                    for url in generator:
                        self.add_request(url)

                now = time.time()
                for client in self.clients:
                    if inflight_list.has_key(client.fileno()):
                        if client.elapsed_seconds(now) > self.timeout:
                            url, ip_address = inflight_list.pop(client.fileno())
                            if not self.quiet:
                                sys.stderr.write('time out on request to [%s] (on %s)\n' % (url, client.fileno()))
                            client.close()
                            splitted = urlparse.urlsplit(url)
                            if not splitted.scheme == 'https':
                                self.retry_with_https(splitted.hostname, url, ip_address)
                            elif not splitted.hostname.startswith('www.'):
                                self.retry_with_www(splitted.hostname, [url])
                    if dispatch_list.has_key(client.fileno()):
                        if client.elapsed_seconds(now) > self.timeout:
                            url, ip_address = dispatch_list.pop(client.fileno())
                            if not self.quiet:
                                sys.stderr.write('time out on connect to [%s] (on %s)\n' % (url, client.fileno()))
                            client.close()
                            splitted = urlparse.urlsplit(url)
                            if not splitted.scheme == 'https':
                                self.retry_with_https(splitted.hostname, url, ip_address)
                            elif not splitted.hostname.startswith('www.'):
                                self.retry_with_www(splitted.hostname, [url])
                    if not client.is_connected():
                        if 0 != len(retry_list):
                            url, ip_address = retry_list.pop()
                            port, is_ssl = self.get_url_port_info(url)
                            if client.connect(ip_address, port, is_ssl):
                                dispatch_list[client.fileno()] = (url, ip_address)
                            else:
                                if not self.quiet:
                                    sys.stderr.write('failed to process [%s] on [%s]\n' % (url, ip_address))
                        else:
                            request = self.next_request()
                            if request:
                                url, ip_address = request
                                port, is_ssl = self.get_url_port_info(url)
                                if client.connect(ip_address, port, is_ssl):
                                    dispatch_list[client.fileno()] = (url, ip_address)
                                else:
                                    retry_list.append((url, ip_address))

                rlist = [c.fileno() for c in self.clients if c.is_readable()]
                wlist = [c.fileno() for c in self.clients if c.is_writeable()]
                xlist = [c.fileno() for c in self.clients if c.is_connected()]

                if 0 == len(dispatch_list) and 0 == len(retry_list) and 0 == len(inflight_list) and 0 == self.outstanding_requests():
                    sys.stderr.write('finished...\n')
                    return
                elif 0 == len(xlist):
#                    print(dispatch_list, retry_list, inflight_list)
                    sys.stderr.write('waiting...\n')
                    time.sleep(1)
                    continue
                else:
                    pass
#                    print(dispatch_list, retry_list, inflight_list)

#                print(rlist, wlist, xlist)
                rlist, wlist, xlist = select.select(rlist, wlist, xlist, 1)
#                print(rlist, wlist, xlist)

                for client in self.clients:
                    client_fileno = client.fileno()
                    if client_fileno in xlist:
                        # failure
                        client.close()
                    elif client.need_ssl_handshake():
                        if not client.do_handshake():
                            if not self.quiet:
                                sys.stderr.write('failed during handshake for [%s]\n' % client_fileno)
                            client.close()
                    elif client_fileno in rlist:
                        finished, redirect = client.read_response(self.results)
                        if finished:
                            url, ip_address = inflight_list.pop(client_fileno)
                            if redirect and not self.noredirects:
                                orig_splitted = urlparse.urlsplit(url)
                                splitted = urlparse.urlsplit(redirect)
                                same_host = False
                                if splitted.hostname == orig_splitted.hostname:
                                    same_host = True
                                if redirect_list.has_key(splitted.hostname):
                                    if redirect_list[splitted.hostname] < 5:
                                        if same_host:
                                            self.add_resolved_request(redirect, ip_address)
                                        else:
                                            self.add_request(redirect)
                                        redirect_list[splitted.hostname] += 1
                                    else:
                                        if not self.quiet:
                                            sys.stderr.write('too many redirects to [%s]: %s\n' % (splitted.hostname, redirect))
                                else:
                                    if same_host:
                                        self.add_resolved_request(redirect, ip_address)
                                    else:
                                        self.add_request(redirect)
                                    redirect_list[splitted.hostname] = 1
                            else:
                                splitted = urlparse.urlsplit(url)
                                if redirect_list.has_key(splitted.hostname):
                                    redirect_list.pop(splitted.hostname)
                            rcount += 1
                            if 0 == (rcount % self.cut_count):
                                self.close_results()
                                self.open_results()
                    elif client_fileno in wlist:
                        url, ip_address = dispatch_list[client_fileno]
                        sent, ok = client.send_request(url)
                        if sent:
                            dispatch_list.pop(client_fileno)
                            if ok:
                                inflight_list[client_fileno] = (url, ip_address)
                                wcount += 1

            except KeyboardInterrupt:
                sys.stderr.write('processing interrupted\n')
                return
            except Exception, e:
                sys.stderr.write('major problem: %s\nurl=%s, dispatch_list=%s,inflight_list=%s,retry_list=%s,redirect_list=%s\n' % (traceback.format_exc(e), url, dispatch_list, inflight_list, retry_list, redirect_list))
                return

    def process(self):
        self.open_results()
        try:
            self.run_requests(self.request_generator)
        except Exception, e:
            pass
        self.close_results()

if '__main__' == __name__:

    parser = argparse.ArgumentParser(description='Fetch a resource')
    parser.add_argument('hostfile', metavar='hostfile', type=str, help='hostfile', action='store', nargs='?')
    parser.add_argument('-s', '--skip-count', dest='skipcount', type=int, action='store', default=-1)
    parser.add_argument('-t', '--total-count', dest='totalcount', type=int, action='store', default=-1)
    parser.add_argument('-U', '--user-agent', dest='useragent', type=str, action='store', default='Mozilla/5.0 RSpider/1.0')
    parser.add_argument('-m', '--method', dest='method', type=str, action='store', default='GET')
    parser.add_argument('-p', '--path', dest='path', type=str, action='store', default='/robots.txt')
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true')
    parser.add_argument('-H', '--header', dest='headers', type=str, action='append')
    parser.add_argument('-nR', '--no-redirects', action='store_true', dest='noredirects')
    parser.add_argument('-nS', '--no-ssl', action='store_true', dest='nossl')
    parser.add_argument('--timeout', dest='timeout', type=int, action='store', default=10)
    parser.add_argument('--clients', dest='clients', type=int, action='store', default=15)
    
    args = parser.parse_args()
    print(args)
    if args.hostfile:
        pass
    else:
        parser.print_usage()
        print('\nNeed hostfile\n')
        sys.exit(1)
    
    rspider = RSpider(args.hostfile, args.totalcount, args.skipcount, args.method, args.path, args.useragent, args.headers, args.noredirects, args.nossl, args.timeout, args.clients, args.quiet)
    rspider.process()
