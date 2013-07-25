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
from PyQt4.QtCore import Qt, QObject, SIGNAL, QThread, QTimer, QMutex, QUrl
from PyQt4.QtGui import *


from core.database.constants import *
from core.fuzzer.RequestRunner import RequestRunner
from core.network.InMemoryCookieJar import InMemoryCookieJar
from core.crawler.FormFiller import FormFiller
from core.crawler.SpiderRules import SpiderRules

import re
import urllib.request, urllib.error, urllib.parse
from urllib import parse as urlparse
from io import StringIO
from collections import deque
import uuid

class SpiderThread(QThread):

    def __init__(self, framework, queueDataModel, pendingResponsesDataModel, pendingAnalysisDataModel, internalStateDataModel, parent = None):
        QThread.__init__(self, parent)
        self.framework = framework
        self.queueDataModel = queueDataModel
        self.pendingResponsesDataModel = pendingResponsesDataModel
        self.pendingAnalysisDataModel = pendingAnalysisDataModel
        self.internalStateDataModel = internalStateDataModel

        self.qlock = QMutex()
        self.qlock_analysis = QMutex()
        QObject.connect(self, SIGNAL('quit()'), self.quitHandler)
        QObject.connect(self, SIGNAL('started()'), self.startedHandler)

    def do_setup(self):

        self.spider_items = {}
        self.spider_outstanding_requests = {}

        self.analysis_queue = deque()

        self.scopeController = self.framework.getScopeController()
        self.contentExtractor = self.framework.getContentExtractor()
        self.htmlExtractor = self.contentExtractor.getExtractor('html')
        self.spiderConfig = self.framework.getSpiderConfig()
        self.spiderRules = SpiderRules(self.framework, self)
        self.formFiller = FormFiller(self.framework, self)

        self.re_location_header = re.compile(r'^Location:\s*(.+)$', re.I)
        self.re_content_location_header = re.compile(r'^Content-Location:\s*(.+)$', re.I)

        self.Data = None
        self.read_cursor = None
        self.read_cursor2 = None
        self.write_cursor = None

        self.keep_spidering = False

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.read_cursor = self.Data.allocate_thread_cursor()
        self.read_cursor2 = self.Data.allocate_thread_cursor()
        self.write_cursor = self.Data.allocate_thread_cursor()
        self.populateExistingSpiderData()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.write_cursor and self.Data:
            self.write_cursor.close()
            self.Data.release_thread_cursor(self.write_cursor)
            self.write_cursor = None
        if self.read_cursor2 and self.Data:
            self.read_cursor2.close()
            self.Data.release_thread_cursor(self.read_cursor2)
            self.read_cursor2 = None
        if self.read_cursor and self.Data:
            self.read_cursor.close()
            self.Data.release_thread_cursor(self.read_cursor)
            self.read_cursor = None

    def run(self):
        QObject.connect(self, SIGNAL('populateExistingSpiderData()'), self.do_populateExistingSpiderData, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('clearSpiderQueue()'), self.do_clearSpiderQueue, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('clearSpiderPendingResponses()'), self.do_clearSpiderPendingResponses, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('resetSpiderPendingResponses()'), self.do_resetSpiderPendingResponses, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('startSpidering()'), self.do_startSpidering, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('stopSpidering()'), self.do_stopSpidering, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('spiderItemFinished()'), self.do_spiderItemFinished, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('generateSpiderValues()'), self.do_generateSpiderValues, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('sendNextSpiderRequest()'), self.do_sendNextSpiderRequest, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('addPendingAnalysis()'), self.do_addPendingAnalysis, Qt.DirectConnection)
        self.exec_()

    def quitHandler(self):
        self.framework.debug_log('SpiderThread quit...')
        self.close_cursor()
        self.exit(0)

    def startedHandler(self):
        self.framework.debug_log('SpiderThread started...')
        self.do_setup()
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)
        self.framework.subscribe_populate_spider_response_id(self.do_populate_spider_response_id)
        self.framework.subscribe_populate_spider_response_list(self.do_populate_spider_response_list)

    def populateExistingSpiderData(self):
        QTimer.singleShot(50, self, SIGNAL('populateExistingSpiderData()'))

    def clearSpiderQueue(self):
        QTimer.singleShot(50, self, SIGNAL('clearSpiderQueue()'))

    def clearSpiderPendingResponses(self):
        QTimer.singleShot(50, self, SIGNAL('clearSpiderPendingResponses()'))

    def resetSpiderPendingResponses(self):
        QTimer.singleShot(50, self, SIGNAL('resetSpiderPendingResponses()'))

    def startSpidering(self, spider_callback, sequence_id, cookieJar):
        print('startSpidering')
        self.spider_callback = spider_callback
        if sequence_id and sequence_id > 0:
            self.sequence_id = sequence_id
        else:
            self.sequence_id = None
        self.cookieJar = cookieJar
        QTimer.singleShot(100, self, SIGNAL('startSpidering()'))

    def stopSpidering(self):
        print('stopSpidering')
        self.keep_spidering = False
        QTimer.singleShot(50, self, SIGNAL('stopSpidering()'))

    def spiderItemFinished(self, response_id):
###->        print('*****1')
        self.qlock.lock()
###->        print('*****2')
        try:
###->            print('*****3')
            self.Data.update_spider_pending_response_id(self.write_cursor, 'C', response_id, 'render')
###->            print('*****4')
        finally:
            self.qlock.unlock()
###->        print('*****5')
        self.handle_spider_available()

    def do_startSpidering(self):
        print('do_startSpidering')
        # TODO: decide about global cookies ?
        self.requestRunner = RequestRunner(self.framework, self)
        self.requestRunner.setup(self.network_response_received, self.cookieJar, self.sequence_id)
        self.keep_spidering = True
        self.renderer_available = False
        self.handle_spider_available()

    def do_spiderItemFinished(self):
        pass
###->        print('****6')

    def handle_spider_available(self):
        if self.keep_spidering:
            QTimer.singleShot(10, self, SIGNAL('generateSpiderValues()'))
            do_send = False
            self.qlock.lock()
            try:
                if len(self.spider_outstanding_requests) == 0:
                    do_send = True
            finally:
                self.qlock.unlock()
            if do_send:
                QTimer.singleShot(10, self, SIGNAL('sendNextSpiderRequest()'))

            self.dispatch_next_render_item()

    def do_populate_spider_response_id(self, response_id):
        self.qlock.lock()
        try:
            self.add_pending_spider_response(response_id, 0)
        finally:
            self.qlock.unlock()

        QTimer.singleShot(50, self, SIGNAL('generateSpiderValues()'))

    def do_populate_spider_response_list(self, id_list):
        self.qlock.lock()
        try:
            for response_id in id_list:
                self.add_pending_spider_response(int(response_id), 0)
                self.add_pending_spider_response(int(response_id), 0)
        finally:
            self.qlock.unlock()

        QTimer.singleShot(50, self, SIGNAL('generateSpiderValues()'))

    def add_pending_spider_response(self, response_id, depth):
        row = self.Data.read_responses_by_id(self.read_cursor, response_id)
        if not row:
            self.framework.log_warning('missing response id: %s' % (response_id))
            return

        response_items = [m or '' for m in row]
        content_type = str(response_items[ResponsesTable.RES_CONTENT_TYPE])
        content_type, charset = self.contentExtractor.parseContentType(content_type)
        base_type = self.contentExtractor.getBaseType(content_type)
        if 'html' == base_type:
            self.add_pending_spider_response_id(response_id, 'spider', depth)
            self.add_pending_spider_response_id(response_id, 'render', depth)
        else:
            # TODO: implement other render types
            self.add_pending_spider_response_id(response_id, 'spider', depth)
            self.framework.log_warning('skipping unsupported type for render analysis for [%s]: %s' % (response_id, content_type))

    def add_pending_spider_response_id(self, response_id, request_type, depth):
        data_item = [response_id, request_type, depth, 'P']
        if self.Data.add_spider_pending_response_id(self.write_cursor, data_item):
            self.pendingResponsesDataModel.append_data([data_item])

    def do_generateSpiderValues(self):
        self.generate_from_pending_responses()
        self.generate_from_pending_analysis()

    def generate_from_pending_responses(self):
        self.qlock.lock()
        keep_looping = True
        try:
            putback_rows = []
            print('generate spider values from pending responses')
            while keep_looping:
                data_item = self.pendingResponsesDataModel.popleft_data()
###->                print(data_item)
                if data_item:
                    response_id, request_type, depth, status = data_item
                else:
                    keep_looping = False

                if data_item is not None:
                    if 'spider' == request_type:
                        self.generate_spider_values(response_id, depth)
                        # remove from database
                        self.Data.update_spider_pending_response_id(self.write_cursor, 'C', response_id, request_type)
                    else:
                        # put back
                        putback_rows.append(data_item)

            self.pendingResponsesDataModel.append_data(putback_rows)

        except Exception as error:
            self.framework.report_exception(error)
        finally:
            self.qlock.unlock()

    def generate_from_pending_analysis(self):
        keep_looping = True
        self.qlock.lock()
        try:
            print('generate spider values from analysis queues')
            while self.keep_spidering and keep_looping:
                data_item = self.pendingAnalysisDataModel.popleft_data()
###->                print(data_item)

                if data_item:
                    analysis_id, analysis_type, content, url, depth = data_item
                    if depth:
                        new_depth = int(depth) + 1
                    else:
                        new_depth = 1
                    if new_depth < self.spiderConfig.max_link_depth:
                        spider_requests = self.calculate_spider_requests_from_analysis(data_item)
                        self.add_spider_requests(spider_requests, url, new_depth)
                    self.Data.delete_spider_pending_analysis(self.write_cursor, analysis_id)
                else:
                    keep_looping = False

        except Exception as error:
            self.framework.report_exception(error)
        finally:
            self.qlock.unlock()

    def dispatch_next_render_item(self):
###->        print('****7')
        if self.keep_spidering:
###->            print('****8')
            render_item = self.get_next_render_item()
            if render_item:
                self.renderer_available = False
                QObject.emit(self.spider_callback, SIGNAL('spiderItemAvailable(int, QString, QUrl, int)'), render_item[0], render_item[1], render_item[2], render_item[3])
            else:
                self.renderer_available = True

    def do_sendNextSpiderRequest(self):
        while True:
            spider_request = self.get_next_spider_request()
###->            print(spider_request)
            if not spider_request:
                return
            if spider_request:
                method, url, headers, body, context = spider_request
                if self.scopeController.isUrlInScope(url, url):
                    self.requestRunner.queue_request(method, url, headers, body, context)
                    return
                else:
                    self.framework.log_warning('SKIPPING out of scope: [%s]' % (url))
                    self.qlock.lock()
                    try:
                        data_item = self.spider_outstanding_requests.pop(context)
                        self.Data.update_spider_queue_item_status(self.write_cursor, int(data_item[SpiderQueueTable.ID]), 'C') 
                    except KeyError:
                        pass
                    finally:
                        self.qlock.unlock()

    def network_response_received(self, response_id, context):
        data_item = None
        context = str(context)
        if context:
            self.qlock.lock()
            try:
                if context not in self.spider_outstanding_requests:
                    self.framework.log_warning('*** missing spider request for [%s]' % (context))
                else:
                    data_item = self.spider_outstanding_requests.pop(context)
                    self.Data.update_spider_queue_item_status(self.write_cursor, int(data_item[SpiderQueueTable.ID]), 'C') 

                    self.add_pending_spider_response_id(response_id, 'spider', int(data_item[SpiderQueueTable.DEPTH]))
                    self.add_pending_spider_response_id(response_id, 'render', int(data_item[SpiderQueueTable.DEPTH]))
                
            finally:
                self.qlock.unlock()

        if self.keep_spidering:
            QTimer.singleShot(50, self, SIGNAL('generateSpiderValues()'))
            QTimer.singleShot(50, self, SIGNAL('sendNextSpiderRequest()'))
            # TODO: checking concurrency issues
            if self.renderer_available:
                self.dispatch_next_render_item()

    def get_next_render_item(self):
        render_item = None
        self.qlock.lock()
        keep_looping = True
        try:
            putback_rows = []
            while keep_looping:
                data_item = self.pendingResponsesDataModel.popleft_data()
###->                print(data_item)
                if data_item:
                    response_id, request_type, depth, status = data_item
                else:
                    keep_looping = False

                if data_item is not None:
                    if 'render' == request_type:

                        row = self.Data.read_responses_by_id(self.read_cursor, response_id)
                        if not row:
                            self.framework.log_warning('missing response id: %s' % (response_id))
                            continue

                        response_items = [m or '' for m in row]
                        qurl = QUrl.fromEncoded(response_items[ResponsesTable.URL])
                        dataContent = str(response_items[ResponsesTable.RES_DATA])

                        render_item = (response_id, dataContent, qurl, depth) 
                        keep_looping = False
                    else:
                        # put back
                        putback_rows.append(data_item)

            self.pendingResponsesDataModel.appendleft_data(putback_rows)

        except Exception as error:
            self.framework.report_exception(error)
        finally:
            self.qlock.unlock()

###-->        print('next render item', render_item)
        return render_item

    def get_next_spider_request(self):
        self.qlock.lock()
        spider_request = None
        try:
            data_item = self.queueDataModel.popleft_data()
            if data_item:
                method, target_url, headers, body = self.make_spider_request_content(data_item)
                context = uuid.uuid4().hex
                self.spider_outstanding_requests[context] = data_item

                spider_request = (method, target_url, headers, body, context)

        finally:
            self.qlock.unlock()

###-->        print('next spider_request item', spider_request)
        return spider_request

    def do_stopSpidering(self):
        self.keep_spidering = False
        print(('do_stopSpidering', self, self.keep_spidering))

    def generate_spider_values(self, response_id, depth):
        new_depth = depth + 1
        if new_depth >= self.spiderConfig.max_link_depth:
            return

        row = self.Data.read_responses_by_id(self.read_cursor, response_id)
        if not row:
            self.framework.log_warning('missing response id: %s' % (response_id))
            return
        response_items = [m or '' for m in row]

        url = str(response_items[ResponsesTable.URL])
        response_headers = str(response_items[ResponsesTable.RES_HEADERS])
        response_body = str(response_items[ResponsesTable.RES_DATA])
        content_type = str(response_items[ResponsesTable.RES_CONTENT_TYPE])

        spider_requests = self.calculate_spider_requests(url, response_headers, response_body, content_type, new_depth)
        self.add_spider_requests(spider_requests, url, new_depth)

    def add_spider_requests(self, spider_requests, url, new_depth):
        #             if self.spider_queue.has_key(url):
        #                 # TODO: allow for better rescan in future
        #                 self.framework.log_warning('adding already scanned url [%s] for now' % (url))

        for request in spider_requests:
            queue_item = [None, request[0], request[1], request[2], request[3], request[4], url, 'P', new_depth]
            rowid = self.Data.add_spider_queue_item(
                self.write_cursor, queue_item
                )
            queue_item[0] = rowid
            self.queueDataModel.append_data([queue_item])

    def do_populateExistingSpiderData(self):
###        print('starting populating responses')
        self.qlock.lock()
        try:

            rows = []
            for row in self.Data.get_spider_queue_items(self.read_cursor, 'P'):
                rows.append([m or '' for m in row])
            self.queueDataModel.append_data(rows)

            rows = []
            for row in self.Data.read_spider_pending_responses(self.read_cursor, 'P'):
                response_id = int(row[SpiderPendingResponsesTable.RESPONSE_ID])
                request_type = str(row[SpiderPendingResponsesTable.REQUEST_TYPE])
                depth = int(row[SpiderPendingResponsesTable.DEPTH])
                status = str(row[SpiderPendingResponsesTable.STATUS])
                rows.append([response_id, request_type, depth, status])
            self.pendingResponsesDataModel.append_data(rows)

            rows = []
            for row in self.Data.read_spider_pending_analysis(self.read_cursor):
                analysis_id = int(row[SpiderPendingAnalysisTable.ID])
                analysis_type = str(row[SpiderPendingAnalysisTable.ANALYSIS_TYPE])
                content = str(row[SpiderPendingAnalysisTable.CONTENT])
                url = str(row[SpiderPendingAnalysisTable.URL])
                depth = int(row[SpiderPendingAnalysisTable.DEPTH])
                data_item = [analysis_id, analysis_type, content, url, depth]
                rows.append(data_item)
            self.pendingAnalysisDataModel.append_data(rows)

        finally:
            self.qlock.unlock()

###        print('finished populating responses')

    def do_clearSpiderQueue(self):
        self.qlock.lock()
        try:
            self.Data.clear_spider_queue(self.write_cursor)
            self.queueDataModel.clearModel()
        finally:
            self.qlock.unlock()

    def do_clearSpiderPendingResponses(self):
        self.qlock.lock()
        try:
            self.Data.clear_spider_pending_responses(self.write_cursor)
            self.pendingResponsesDataModel.clearModel()
        finally:
            self.qlock.unlock()

    def do_resetSpiderPendingResponses(self):
        self.qlock.lock()
        try:
            self.Data.reset_spider_pending_responses(self.write_cursor)
            self.pendingResponsesDataModel.clearModel()
        finally:
            self.qlock.unlock()

    def calculate_spider_requests(self, url, headers, body, content_type, depth):
        requests = []

        requests.extend(self.process_http_headers(url, headers))

        content_type, charset = self.contentExtractor.parseContentType(content_type)
        base_type = self.contentExtractor.getBaseType(content_type)
        if 'html' == base_type:
            requests.extend(self.process_html_data(url, body, charset))
        else:
            # TODO: implement other types
            self.framework.log_warning('skipping unsupported type for request for [%s]: %s' % (url, content_type))

        return self.filter_spider_requests(requests, depth)

    def calculate_spider_requests_from_analysis(self, analysis_item):

        requests = []
#-->        print('ANALYSIS ->', analysis_item)
        analysis_id, analysis_type, content, url, depth = analysis_item
        depth = int(depth)
        if 'url' == analysis_type:
            self.append_url_link_request(requests, url, content)
        elif 'html' == analysis_type:
            requests.extend(self.process_html_data(url, content, 'utf-8')) # TODO: could extract ?
        elif 'response_id' == analysis_type:
            response_id = int(content)
            self.add_pending_spider_response_id(response_id, 'spider', depth+1)
            self.add_pending_spider_response_id(response_id, 'render', depth+1)
        else:
            self.framework.log_warning('unhandled data_type: %s' % (data_type))

        return self.filter_spider_requests(requests, depth)

    def filter_spider_requests(self, requests, depth):
        # make sure that request has not already been retrieved
        filtered_requests = []
        already_seen = {}
        found_response_id = None
        for request in requests:
            print(('filter spider request', request))
            method, base_url, query = request[0], request[1], request[2]
            if query:
                base_url += '?' + query
            content_type = ''
            if already_seen.get(base_url) == method:
                found = True
            else:
                already_seen[base_url] = method
                found = False
                for row in self.Data.read_responses_by_url(self.read_cursor, base_url):
                    response_items = [m or '' for m in row]
                    if response_items[ResponsesTable.REQ_METHOD] == method:
                        content_type = str(response_items[ResponsesTable.RES_CONTENT_TYPE])
                        found = True
                        found_response_id = int(response_items[ResponsesTable.ID])
                        break
            if not found:
                # TODO: probably shouldn't go back to database for this ....
                for row in self.Data.read_spider_queue_by_url(self.read_cursor, base_url):
                    response_items = [m or '' for m in row]
                    if response_items[SpiderQueueTable.STATUS] != 'D' and response_items[SpiderQueueTable.METHOD] == method:
                        found = True
                        break
            if not found:
                if self.spiderRules.should_include_url(base_url):
                    filtered_requests.append(request)
            elif found_response_id:
                if not self.Data.spider_pending_response_exists(self.read_cursor2, found_response_id, 'spider'):
                    self.add_pending_spider_response_id(found_response_id, 'spider', depth)
                # TODO: fix this hack
                if 'html' in content_type.lower():
                    if not self.Data.spider_pending_response_exists(self.read_cursor2, found_response_id, 'render'):
                        self.add_pending_spider_response_id(found_response_id, 'render', depth)

        return filtered_requests

    def process_http_headers(self, url, headers):
        links = []
        for line in headers.splitlines():
            m = self.re_location_header.match(line)
            if m:
                links.append(m.group(1))
                continue
            m = self.re_content_location_header.match(line)
            if m:
                links.append(m.group(1))
                continue
        if 0 == len(links):
            return []

        requests = []
        for link in links:
            self.append_url_link_request(requests, url, link)
        return requests

    def append_url_link_request(self, requests, base_url, link):
        resolved_url = urlparse.urljoin(base_url, link)
        if not self.scopeController.isUrlInScope(resolved_url, base_url):
            return
        splitted = urlparse.urlsplit(resolved_url)
        if splitted.scheme in ('http', 'https'):
            # TODO: check query for unique parameters
            url = urlparse.urlunsplit((splitted.scheme, splitted.netloc, splitted.path, '', ''))
            requests.append(('GET', url, splitted.query, '', ''))

    def process_html_data(self, url, body, charset):
        requests = []

        results = self.htmlExtractor.process(body, url, charset, None)
        # TODO: check fingerprints here ?

        for link in results.links:
            # TODO: all links should be already resolved ?
            self.append_url_link_request(requests, url, link)

        for form in results.forms:
            link = form.action
            if not self.scopeController.isUrlInScope(link, url):
                continue
            splitted = urlparse.urlsplit(link)
            if splitted.scheme in ('http', 'https'):
                # TODO: check query and form for unique parameters
                base_url = urlparse.urlunsplit((splitted.scheme, splitted.netloc, splitted.path, '', ''))
                form_data = self.get_form_data(form)
                requests.append((form.method.upper(), base_url, splitted.query, form.enctype, form_data))

        return requests

    def get_form_data(self, form):
        body_io = StringIO()
        # TODO: spidering does not support uploading file data
        # create all parameters as named/value parameters, if multipart enctype, generate that when sending
        for i in range(0, len(form.inputs)):
            name, value = self.get_form_input_value(form.inputs[i])
            if 0 != i:
                body_io.write('&')
            if value is not None:
                body_io.write('%s=%s' % (urllib.parse.quote(name), urllib.parse.quote(value)))
            else:
                body_io.write('%s' % (urllib.parse.quote(name)))

        return body_io.getvalue()
        
    def get_form_input_value(self, input):
        # TODO: consider values without names?
        if self.spiderConfig.use_data_bank:
            name = input.name
            value, fill_type = self.formFiller.populate_form_value(input.name, input.Id, input.value, input.Type, input.Class, input.required, input.maxlength, input.accept, input.label)
            if fill_type in ('Username', 'Password') and not self.spiderConfig.submit_user_name_password:
                # use whatever came in 
                value = input.value
        else:
            name = input.name
            if not input.value:
                value = self.formFiller.populate_generic_value(input.name, input.Id, input.value, input.Type, input.Class, input.required, input.maxlength, input.accept, input.label)
            else:
                value = input.value
            
        return name, value

    def make_spider_request_content(self, data_item):
        spider_id, method, url, query_params, encoding_type, form_params, referer, status, depth = data_item
        headers = {}
        if referer:
            headers['Referer']  = referer
        body = ''
        target_url = url
        if query_params:
            target_url += '?' + query_params
        if 'POST' == method:
            headers['Content-Type'] = encoding_type
            if 'application/x-www-form-urlencoded' == encoding_type:
                body = form_params
            else:
                # TODO: implement
                raise Exception('implement me multiparm')

        return method, target_url, headers, body
            
    def process_page_html_content(self, html, url, depth):
        self.qlock_analysis.lock()
        try:
            analysis_item = ['html', html, url, depth]
            self.analysis_queue.append(analysis_item)
        finally:
            self.qlock_analysis.unlock()

        QTimer.singleShot(10, self, SIGNAL('addPendingAnalysis()'))

    def process_page_url_link(self, url, link, depth):
        self.qlock_analysis.lock()
        try:
            analysis_item = ['url', link, url, depth]
            self.analysis_queue.append(analysis_item)
        finally:
            self.qlock_analysis.unlock()

        QTimer.singleShot(10, self, SIGNAL('addPendingAnalysis()'))
            
    def process_page_response_id(self, response_id, depth):
        self.qlock_analysis.lock()
        try:
            analysis_item = ['response_id', str(response_id), '', depth]
            self.analysis_queue.append(analysis_item)
        finally:
            self.qlock_analysis.unlock()

        QTimer.singleShot(10, self, SIGNAL('addPendingAnalysis()'))

    def do_addPendingAnalysis(self):
        self.qlock_analysis.lock()
        try:
            self.qlock.lock()
            try:
                rows = []
                while (len(self.analysis_queue) > 0):
                    analysis_item = self.analysis_queue.popleft()
                    data_item = [None, analysis_item[0], analysis_item[1], analysis_item[2], analysis_item[3]]
                    rowid = self.Data.add_spider_pending_analysis(self.write_cursor, data_item)
                    data_item[0] = rowid
                    rows.append(data_item)
                self.pendingAnalysisDataModel.append_data(rows)
            finally:
                self.qlock.unlock()
        finally:
            self.qlock_analysis.unlock()

