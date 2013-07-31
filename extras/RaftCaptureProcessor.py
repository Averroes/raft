#
# A Python 3 urllib compatible processor module to generate RAFT capture files
#
# Copyright (c) 2011-2013 by RAFT Team
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE
# 

import urllib.request, urllib.error, urllib.parse
import io
import os
import time
import sys
import lzma
import re
import string
import threading
import base64
from urllib import parse as urlparse
from xml.sax.saxutils import escape, quoteattr

class RaftCaptureProcessor(urllib.request.BaseHandler):
    class _wrapper(io.BytesIO):
        def __init__(self, parent, request, response):
            request = request
            self.response = response
            data = parent.write_capture(request, response)
            io.BytesIO.__init__(self, data)

        def __getattr__(self, name):
            return getattr(self.response,name)

    def __init__(self, directory, cut_count = 10000):
        self.lock = threading.Lock()
        self.directory = directory
        self.re_nonprintable = re.compile(bytes('[^%s]' % re.escape('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r'), 'ascii'))
        self.re_nonprintable_str = re.compile('[^%s]' % re.escape('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r'))
        self.cut_count = cut_count # TODO: add max size as well
        self.open_file()
    
    def open_file(self):
        now = time.time()
        self.filename = os.path.join(self.directory, 'RaftCapture-{0}.xml.xz'.format(int(now*1000)))
        self.ofhandle = lzma.LZMAFile(self.filename, 'wb')
        self.ofhandle.write(b'<raft version="1.0">\n')
        self.write_count = 0
        
    def close(self):
        self.ofhandle.write(b'</raft>')
        self.ofhandle.close()

    def http_request(self, req):
        return req

    def http_response(self, req, response):
        return RaftCaptureProcessor._wrapper(self, req, response)

    def https_request(self, req):
        return req

    def https_response(self, req, response):
        return RaftCaptureProcessor._wrapper(self, req, response)

    def write_capture(self, request, response):
        acquired = False
        try:
            acquired = self.lock.acquire()
            return self.__write_capture(request, response)
        finally:
            if acquired:
                self.lock.release()

    def __write_capture(self, request, response):

        ohandle = io.StringIO()
        response_body = b''
        saved_exception = None
        try:
            ohandle.write('<capture>\n')
            ohandle.write('<request>\n')
            method = request.get_method()
            url = request.get_full_url() 
            parsed = urlparse.urlsplit(url)
            relative_url = parsed.path
            if parsed.query:
                relative_url += '?' + parsed.query
            if parsed.fragment:
                # TODO: will this ever happen?
                relative_url += '#' + parsed.fragment

            ohandle.write('<method>%s</method>\n' % escape(method))
            ohandle.write('<url>%s</url>\n' % escape(url))
            ohandle.write('<host>%s</host>\n' % escape(request.get_host()))
            try:
                # ghetto
                addr = response.fp.raw._sock.getpeername()
                if addr:
                    ohandle.write('<hostip>%s</hostip>\n' % escape(addr[0]))
            except Exception as error:
                pass
            ohandle.write('<datetime>%s</datetime>\n' % escape(time.asctime(time.gmtime())+' GMT')) # TODO: can we calculate request time and elapsed?
            request_headers = '%s %s HTTP/1.1\r\n' % (method, relative_url) # TODO: is there access to the HTTP version?
            for item in request.header_items():
                request_headers += item[0] + ': ' + '\r\n\t'.join(item[1:]) + '\r\n'

            if self.re_nonprintable_str.search(request_headers):
                ohandle.write('<headers encoding="base64">%s</headers>\n' % base64.b64encode(request_headers.encode('utf-8')).decode('ascii'))
            else:
                ohandle.write('<headers>%s</headers>\n' % escape(request_headers))
            if request.has_data():
                request_body = request.get_data()
                if self.re_nonprintable.search(request_body):
                    ohandle.write('<body encoding="base64">%s</body>\n' % base64.b64encode(request_body).decode('ascii'))
                else:
                    ohandle.write('<body>%s</body>\n' % escape(request_body.decode('ascii')))
            ohandle.write('</request>\n')
            ohandle.write('<response>\n')
            status = int(response.getcode())
            ohandle.write('<status>%d</status>\n' % status)
            headers = response.info()
            if 'HEAD' == method or status < 200 or status in (204, 304,):
                response_body = b''
            else:
                try:
                    response_body = response.read()
                except urllib2.IncompleteRead as e:
                    saved_exception = e
            response_headers = 'HTTP/1.1 %d %s\r\n' % (status, response.msg) # TODO: is there access to the HTTP version?
            response_headers += headers.as_string()
            content_type = headers.get('Content-Type')
            content_length = headers.get('Content-Length')

            if content_type:
                ohandle.write('<content_type>%s</content_type>\n' % escape(content_type))
            if content_length:
                ohandle.write('<content_length>%d</content_length>\n' % int(content_length))

            if self.re_nonprintable_str.search(response_headers):
                ohandle.write('<headers encoding="base64">%s</headers>\n' % base64.b64encode(response_headers.encode('utf-8')).decode('ascii'))
            else:
                ohandle.write('<headers>%s</headers>\n' % escape(response_headers))
            if response_body:
                if self.re_nonprintable.search(response_body):
                    ohandle.write('<body encoding="base64">%s</body>\n' % base64.b64encode(response_body).decode('ascii'))
                else:
                    ohandle.write('<body>%s</body>\n' % escape(response_body.decode('ascii')))

            ohandle.write('</response>\n')
            ohandle.write('</capture>\n')

            self.ofhandle.write(ohandle.getvalue().encode('utf-8'))
            ohandle.close()
            
            self.write_count += 1
            if 0 == (self.write_count % self.cut_count):
                self.close()
                self.open_file()

        except Exception as e:
            sys.stderr.write('*** unhandled error in RaftCaptureProcessor: %s\n' % (e))

        if saved_exception:
            raise(saved_exception)

        return response_body

class IgnoreRedirect(urllib.request.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, hdrs):
        return fp
    def http_error_302(self, req, fp, code, msg, hdrs):
        return fp
    def http_error_303(self, req, fp, code, msg, hdrs):
        return fp
    def http_error_307(self, req, fp, code, msg, hdrs):
        return fp
        
if '__main__' == __name__:

    # test and sample code

    from contextlib import closing

    if len(sys.argv) == 1:
        targets = ['www.bing.com']
    else:
        count = 0
        targets = []
        for line in open(sys.argv[1], 'r'):
            hostname = line.rstrip()
            if ',' in hostname:
                hostname = hostname.split(',',1)[1]
            targets.append(hostname)
            count += 1
            if count > 10:
                break

    with closing(RaftCaptureProcessor('.')) as raftCapture:
        # proxyHandler = urllib2.ProxyHandler({'http':'localhost:8080', 'https':'localhost:8080'})
        opener = urllib.request.build_opener(raftCapture, )

        for target in targets:
            url = 'http://'+target+'/'
            req = urllib.request.Request(url)
            req.add_header('User-agent', 'Mozilla/5.0 (Windows NT 5.1; rv:2.0) Gecko/20100101 Firefox/4.0')

            try:
                response = opener.open(req, timeout=5)
            except urllib.error.HTTPError as error:
                response = error
            except urllib.error.URLError as error:
                sys.stdout.write('failed on %s: %s\n' % (url, error))
                sys.stdout.flush()
                response = None

            if False and response:
                print(('%d %s' % (response.getcode(), response.msg)))
                print((''.join(response.headers.headers)))
                print((response.read()))

