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
import sys, bz2, gzip
import re
from urllib import parse as urlparse
import logging, traceback
from io import StringIO
from xml.sax.saxutils import escape
from collections import deque

class appscan_parse_xml():
    """ Parses AppScan XML file into request and result data and vulnerability info"""

    S_INITIAL = 1
    S_XML_REPORT = 2
    S_APP_SCAN_INFO = 3
    S_SUMMARY = 4
    S_RESULTS = 5
    S_ISSUES = 6
    S_ISSUE = 7
    S_VARIANT = 8
    S_APPLICATION_DATA = 10

    re_request_line = re.compile(r'^(OPTIONS|GET|HEAD|POST|PUT|DELETE|TRACE|CONNECT|\w+)\s+((?:http|/).*?)(?:\s+(HTTP/\d\.\d))$')
    re_status_line = re.compile(r'^(HTTP/\d\.\d)\s+(\d{3})(?:\s+(.*))?$')

    def __init__(self, appscanfile):
        if appscanfile.endswith('.xml'):
            self.source = open(appscanfile, 'rb')
        else:
            raise Exception('Unsupported file type for %s' % (appscanfile))

        self.appscanfile = appscanfile

        # http://effbot.org/zone/element-iterparse.htm#incremental-parsing
        self.context = etree.iterparse(self.source, events=('start', 'end'), huge_tree = True)
        self.iterator = iter(self.context)
        self.root = None

        # results storage
        self.results_queue = deque()

        self.version = 2
        self.states = [self.S_INITIAL]
        self.state_table = {
            self.S_INITIAL : (
                ('start', 'XmlReport', self.xml_report_start),
                ),
            self.S_XML_REPORT : (
                ('start', 'AppScanInfo', self.app_scan_info_start),
                ('start', 'Summary', self.summary_start),
                ('start', 'Results', self.results_start),
                ('start', 'ApplicationData', self.application_data_start),
                ('end', 'XmlReport', self.xml_report_end),
                ),
            self.S_APP_SCAN_INFO : (
                ('start', '*', self.app_scan_info_node_start),
                ('end', '*', self.app_scan_info_node_end),
                ('end', 'AppScanInfo', self.app_scan_info_end),
                ),
            self.S_SUMMARY : (
                ('start', '*', self.summary_node_start),
                ('end', '*', self.summary_node_end),
                ('end', 'Summary', self.summary_end),
                ),
            self.S_RESULTS : (
                ('start', 'Issues', self.issues_start),
                ('start', '*', self.results_node_start),
                ('end', '*', self.results_node_end),
                ('end', 'Results', self.results_end),
                ),
            self.S_ISSUES : (
                ('start', 'Issue', self.issue_start),
                ('start', '*', self.issues_node_start),
                ('end', '*', self.issues_node_end),
                ('end', 'Issues', self.issues_end),
                ),
            self.S_ISSUE : (
                ('start', 'Variant', self.variant_start),
                ('start', '*', self.issue_node_start),
                ('end', '*', self.issue_node_end),
                ('end', 'Issue', self.issue_end),
                ),
            self.S_VARIANT : (
                ('start', '*', self.variant_node_start),
                ('end', '*', self.variant_node_end),
                ('end', 'Variant', self.variant_end),
                ),
            self.S_APPLICATION_DATA : (
                ('start', '*', self.application_data_node_start),
                ('end', '*', self.application_data_node_end),
                ('end', 'ApplicationData', self.application_data_end),
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

    def xml_report_start(self, elem):
        self.root = elem
        self.states.append(self.S_XML_REPORT)

    def xml_report_end(self, elem):
        raise(StopIteration)

    # AppScanInfo
    def app_scan_info_start(self, elem):
        self.states.append(self.S_APP_SCAN_INFO)

    def app_scan_info_node_start(self, elem):
        pass

    def app_scan_info_node_end(self, elem):
        pass

    def app_scan_info_end(self, elem):
        self.states.pop()

    # Summary
    def summary_start(self, elem):
        self.states.append(self.S_SUMMARY)

    def summary_node_start(self, elem):
        pass

    def summary_node_end(self, elem):
        pass

    def summary_end(self, elem):
        self.states.pop()

    # Results
    def results_start(self, elem):
        self.states.append(self.S_RESULTS)

    def results_node_start(self, elem):
        pass

    def results_node_end(self, elem):
#        print('results', elem.tag)
        pass

    def results_end(self, elem):
        self.states.pop()

    # Issues
    def issues_start(self, elem):
        self.states.append(self.S_ISSUES)

    def issues_node_start(self, elem):
        pass

    def issues_node_end(self, elem):
#        print('issues', elem.tag)
        pass

    def issues_end(self, elem):
        self.states.pop()

    # Issue
    def issue_start(self, elem):
        self.states.append(self.S_ISSUE)
        self.current_issue = {
            'IssueTypeID' : elem.attrib.get('IssueTypeID'),
            'Noise' : elem.attrib.get('Noise'),
            'Url' : '',
            'Severity' : '',
            'Entity_Name' : '',
            'Entity_Type' : '',
            'variants' : []
            }

    def issue_node_start(self, elem):
        pass

    def issue_node_end(self, elem):
        if 'Url' == elem.tag:
            self.current_issue['Url'] = str(elem.text)
        elif 'Severity' == elem.tag:
            self.current_issue['Severity'] = str(elem.text)
        elif 'Entity' == elem.tag:
            if 'Name' in elem.attrib:
                self.current_issue['Entity_Name'] = elem.attrib.get('Name')
            if 'Type' in elem.attrib:
                self.current_issue['Entity_Type'] = elem.attrib.get('Type')
        else:
            sys.stderr.write('Unexpected Issue node: %s\n' % (elem.tag))

    def issue_end(self, elem):
        elem.clear()
        self.root.clear()
        self.states.pop()
#        print(self.current_issue['variants'])
        return self.make_results()

    # Variant
    def variant_start(self, elem):
        self.states.append(self.S_VARIANT)
        self.current_variant = {
            'ID' : elem.attrib.get('ID'),
            'Comments' : '',
            'Difference' : '',
            'Reasoning' : '',
            'AdditionalData' : '',
            'CWE' : '',
            'CVE' : '',
            'validations' : [],
            'results' : []
            }

    def variant_node_start(self, elem):
        pass

    def variant_node_end(self, elem):
        if 'Comments' == elem.tag:
            self.current_variant['Comments'] = str(elem.text)
        elif 'Difference' == elem.tag:
            self.current_variant['Difference'] = str(elem.text)
        elif 'Reasoning' == elem.tag:
            self.current_variant['Reasoning'] = str(elem.text)
        elif 'AdditionalData' == elem.tag:
            self.current_variant['AdditionalData'] = str(elem.text)
        elif 'CWE' == elem.tag:
            self.current_variant['CWE'] = str(elem.text)
        elif 'CVE' == elem.tag:
            self.current_variant['CVE'] = str(elem.text)
        elif 'ValidationDataLocationAtTestResponse' == elem.tag:
            pass
        elif 'Validation' == elem.tag:
            pass
        elif 'OriginalHttpTraffic' == elem.tag:
            self.extract_results_from_traffic(elem.text)
        elif 'TestHttpTraffic' == elem.tag:
            self.extract_results_from_traffic(elem.text)
        else:
            sys.stderr.write('Unexpected Variant node: %s\n' % (elem.tag))

    def variant_end(self, elem):
        self.current_issue['variants'].append(self.current_variant)
        self.states.pop()

    # Application_Data
    def application_data_start(self, elem):
        self.states.append(self.S_APPLICATION_DATA)

    def application_data_node_start(self, elem):
        pass

    def application_data_node_end(self, elem):
        pass

    def application_data_end(self, elem):
        self.states.pop()

    def make_results(self):
        results = []
        for variant in self.current_issue['variants']:
            for result in variant['results']:
                method, url, host, status, datetime, content_type, content_length, request_headers, request_body, response_headers, response_body = result
                hostip = ''
                request = [bytes(request_headers, 'utf-8', 'ignore'), bytes(request_body, 'utf-8', 'xmlcharrefreplace')]
                response = [bytes(response_headers, 'utf-8', 'ignore'), bytes(response_body, 'utf-8', 'xmlcharrefreplace')]
                results.append(('APPSCAN_XML_VARIANT', host, hostip, url, status, datetime, request, response, method, content_type, {'content_length':content_length }))
        return results
                            
    def add_traffic_results(self, method, url, host, status, datetime, content_type, content_length, request_headers, request_body, response_headers, response_body):
        self.current_variant['results'].append([method, url, host, status, datetime, content_type, content_length, request_headers, request_body, response_headers, response_body])

    def extract_results_from_traffic(self, raw_traffic):

        try:
            traffic = str(raw_traffic)
        except UnicodeEncodeError:
            traffic = raw_traffic.encode('utf-8', 'ignore')

        base_scheme = 'http'
        base_url = self.current_issue['Url']
        if base_url:
            splitted = urlparse.urlsplit(base_url)
            base_scheme = splitted.scheme

        # process request and response
        has_request_headers = False
        has_request_line = False
        has_status_line = False
        lastpos = -1
#        for rawline in traffic.splitlines():
        request_headers_io = None
        pos = traffic.find('\n')
        while pos != -1:
            rawline = traffic[lastpos+1:pos+1]
            lastpos = pos
            pos = traffic.find('\n', lastpos+1)
            line = rawline.rstrip()
            status_line_match = None
            if self.re_request_line.match(line):
                if has_request_headers:
                    response_body = response_body_io.getvalue()
                    self.add_traffic_results(method, url, host, status, datetime, content_type, content_length, request_headers, request_body, response_headers, response_body)
                has_request_line = False
                has_status_line = False
                has_request_headers = False
                has_request_body = False
                has_response_headers = False
                has_response_body = False
                url = None
                request_url, method, host, http_version = '', '', '', ''
                datetime, status, content_length, content_type = '', '', '', ''
                request_headers, request_body, response_headers, response_body = '', '', '', ''
                request_headers_io = StringIO()
                response_headers_io = StringIO()
                request_body_io = StringIO()
                response_body_io = StringIO()
                req_length = -1
                res_length = -1
                request_headers, request_body, response_headers, response_body = '', '', '', ''
            elif has_request_headers and not has_status_line:
                status_line_match = self.re_status_line.match(line)
                if status_line_match:
                    has_request_headers = True
                    has_request_body = True
                    request_body = request_body_io.getvalue()

                    has_response_headers = False
                    has_response_body = False

            if not has_request_headers:
                if not request_headers_io:
                    request_headers_io = StringIO()
                request_headers_io.write(line + '\r\n')
                if not line or 0 == len(line):
                    if not has_request_line:
                        continue
                    has_request_headers = True
                    request_headers = request_headers_io.getvalue()
                    if request_url:
                        splitted = urlparse.urlsplit(request_url)
                        if splitted.hostname:
                            host = splitted.hostname
                        scheme = splitted.scheme or base_scheme
                        url = urlparse.urlunsplit((scheme, host, splitted.path, splitted.query, ''))
                    else:
                        url = base_url
#                    print(method, url, request_headers)
                    if req_length > 0:
                        pass
                    else:
                        request_body = ''
                        has_request_body = True
                else:
                    m = self.re_request_line.match(line)
                    if m:
                        has_request_line = True
                        method = m.group(1)
                        request_url = m.group(2)
                        http_version = m.group(3)
                    elif ':' in line:
                        name, value = [m.strip() for m in line.split(':', 1)]
                        lname = name.lower()
                        if not host and 'host' == lname:
                            host = value.strip()
                        elif 'content-length' == lname and value != '':
                            req_length = int(value)
            elif not has_request_body:
                request_body_io.write(rawline)
            elif not has_response_headers:
                if not has_status_line:
                    if not status_line_match:
                        status_line_match = self.re_status_line.match(line)
                    if status_line_match:
                        response_headers_io.write(line + '\r\n')
                        has_status_line = True
                        status = status_line_match.group(2)
                elif not line or 0 == len(line):
                    response_headers_io.write(line + '\r\n')
                    response_headers = response_headers_io.getvalue()
                    has_response_headers = True
                    if res_length > 0:
                        pass
                    else:
                        # no response length ?
                        pass
#                        response_body = ''
#                        has_response_body = True
                elif ':' in line:
                    response_headers_io.write(line + '\r\n')
                    name, value = [m.strip() for m in line.split(':', 1)]
                    lname = name.lower()
                    if 'content-type' == lname:
                        content_type = value
                    elif 'content-length' == lname and value != '':
                        content_length = value
                        res_length = int(value)
                    elif 'date' == lname:
                        datetime = value

            elif not has_response_body:
                response_body_io.write(rawline)

        if lastpos > -1:
            rawline = traffic[lastpos+1:]
            if not has_request_headers:
                pass
            elif not has_request_body:
                request_body_io.write(rawline)
            elif not has_response_headers:
                pass
            elif not has_response_body:
                response_body_io.write(rawline)
                
        if has_request_headers:
            response_body = response_body_io.getvalue()
            self.add_traffic_results(method, url, host, status, datetime, content_type, content_length, request_headers, request_body, response_headers, response_body)
    # ---

    def __iter__(self):
        return self

    def __next__(self):
        while len(self.results_queue) > 0:
            results = self.results_queue.popleft()
            return results

        while True:
            event, elem = next(self.iterator)
            tag = elem.tag
            try:
                state = self.states[-1]
                transitions = self.state_table[state]
                wildcard = None
                results = None
                valid_state = False
                for transition in transitions:
####                    print(transition, event, tag)
                    if transition[0] == event:
                        if '*' == transition[1]:
                            wildcard = transition[2]
                        elif transition[1] == tag:
                            func = transition[2]
                            results = func(elem)
                            valid_state = True
                            break

                if not valid_state and not wildcard:
                    raise Exception('Invalid element: state=%s, event=%s, elem=%s' % (state, event, elem.tag))
                elif not valid_state and wildcard:
                    results = wildcard(elem)

                if results:
                    self.results_queue.extend(results)
                    if len(self.results_queue) > 0:
                        return self.results_queue.popleft()

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
    for result in appscan_parse_xml(filename):
#        print(result)
        count += 1

    print(('processed count: %d' % (count)))

