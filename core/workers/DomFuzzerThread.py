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

import re
from core.database.constants import *
from urllib2 import urlparse
from cStringIO import StringIO
from collections import deque

class DomFuzzerThread(QThread):

    UNIQUE_MARKER_BASE = '\'-(/b41ns5xg,)'
    UNIQUE_MARKER = '>"'+UNIQUE_MARKER_BASE+'<'
    NUM1 = '857345'
    NUM2 = '572912'
    STANDARD_TESTS = ['\'"></script><script>alert(%s)</script>' % NUM1, '\'-alert(%s)-\'' % NUM2, UNIQUE_MARKER]

    def __init__(self, framework, queueDataModel, resultsDataModel, parent = None):
        QThread.__init__(self, parent)
        self.framework = framework
        self.queueDataModel = queueDataModel
        self.resultsDataModel = resultsDataModel
        self.qlock = QMutex()
        self.qlock_analysis = QMutex()
        QObject.connect(self, SIGNAL('quit()'), self.quitHandler)
        QObject.connect(self, SIGNAL('started()'), self.startedHandler)

        self.re_delim = re.compile(r'([;&])')
        self.re_unique_marker_base = re.compile(re.escape(self.UNIQUE_MARKER_BASE), re.I)
        self.pending_fuzz_response_ids = deque()
        self.analysis_queue = deque()

        self.Data = None
        self.read_cursor = None
        self.read_cursor2 = None
        self.write_cursor = None

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.read_cursor = self.Data.allocate_thread_cursor()
        self.read_cursor2 = self.Data.allocate_thread_cursor()
        self.write_cursor = self.Data.allocate_thread_cursor()
        self.populateExistingFuzzData()

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
        QObject.connect(self, SIGNAL('populateExistingFuzzData()'), self.do_populateExistingFuzzData, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('clearFuzzQueue()'), self.do_clearFuzzQueue, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('startFuzzing()'), self.do_startFuzzing, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('stopFuzzing()'), self.do_stopFuzzing, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('fuzzItemFinished()'), self.do_fuzzItemFinished, Qt.DirectConnection)
        QObject.connect(self, SIGNAL('generateFuzzValues()'), self.do_generateFuzzValues, Qt.DirectConnection)
        self.exec_()

    def quitHandler(self):
        self.framework.debug_log('DomFuzzerThread quit...')
        self.close_cursor()
        self.exit(0)

    def startedHandler(self):
        self.framework.debug_log('DomFuzzerThread started...')
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)
        self.framework.subscribe_populate_domfuzzer_response_id(self.do_populate_domfuzzer_response_id)
        self.framework.subscribe_populate_domfuzzer_response_list(self.do_populate_domfuzzer_response_list)

    def populateExistingFuzzData(self):
        QTimer.singleShot(10, self, SIGNAL('populateExistingFuzzData()'))

    def clearFuzzQueue(self):
        QTimer.singleShot(10, self, SIGNAL('clearFuzzQueue()'))

    def startFuzzing(self, fuzz_callback):
        self.fuzz_callback = fuzz_callback
        QTimer.singleShot(10, self, SIGNAL('startFuzzing()'))

    def stopFuzzing(self):
        QTimer.singleShot(10, self, SIGNAL('stopFuzzing()'))

    def fuzzItemFinished(self, fuzz_id, fuzz_url, html, messages):
        self.qlock_analysis.lock()
        self.analysis_queue.append((fuzz_id, fuzz_url, html, messages))
        self.qlock_analysis.unlock()
        QTimer.singleShot(10, self, SIGNAL('fuzzItemFinished()'))

    def do_startFuzzing(self):
        print('do_startFuzzing')
        self.keep_fuzzing = True
        self.dispatch_next_fuzz_item()

    def do_fuzzItemFinished(self):
        self.dispatch_next_fuzz_item()
        self.qlock_analysis.lock()
        try:
            fuzz_id, fuzz_url, html, messages = self.analysis_queue.popleft()
            self.apply_fuzz_analysis(fuzz_id, fuzz_url, html, messages)
            self.Data.update_dom_fuzzer_queue_item_status(self.write_cursor, fuzz_id, 'C')
        finally:
            self.qlock_analysis.unlock()

    def do_populate_domfuzzer_response_id(self, response_id):
        self.qlock.lock()
        try:
            self.pending_fuzz_response_ids.append(response_id)
        finally:
            self.qlock.unlock()

        QTimer.singleShot(10, self, SIGNAL('generateFuzzValues()'))

    def do_populate_domfuzzer_response_list(self, id_list):
        self.qlock.lock()
        try:
            for response_id in id_list:
                self.pending_fuzz_response_ids.append(int(response_id))
        finally:
            self.qlock.unlock()

        QTimer.singleShot(10, self, SIGNAL('generateFuzzValues()'))

    def do_generateFuzzValues(self):
        keep_looping = True
        is_locked = False
        try:
            while keep_looping:
                response_id = None

                self.qlock.lock()
                is_locked = True
                if len(self.pending_fuzz_response_ids) > 0:
                    response_id = self.pending_fuzz_response_ids.popleft()
                else:
                    keep_looping = False

                self.qlock.unlock()
                is_locked = False

                if response_id is not None:
                    self.generate_fuzz_values(response_id)

        finally:
            if is_locked:
                self.qlock.unlock()

    def dispatch_next_fuzz_item(self):
        if self.keep_fuzzing:
            fuzz_item = self.get_next_fuzz_item()
            if fuzz_item:
                QObject.emit(self.fuzz_callback, SIGNAL('fuzzItemAvailable(int, QString, QUrl)'), fuzz_item[0], fuzz_item[1], fuzz_item[2])
            else:
                QObject.emit(self.fuzz_callback, SIGNAL('fuzzRunFinished()'))

    def get_next_fuzz_item(self):
        self.qlock.lock()
        locked = True
        fuzz_item = None
        try:
            data_item = self.queueDataModel.popleft_data()
            if not data_item:
                self.keep_fuzzing = False
                return

            fuzz_id = data_item[DomFuzzerQueueTable.ID]
            row = self.Data.read_responses_by_id(self.read_cursor, data_item[DomFuzzerQueueTable.RESPONSE_ID])

            if not row:
                self.framework.log_warning('missing response id: %s' % (response_id))
                return

            responseItems = [m or '' for m in row]
            target_url = self.compute_url_from_payload(data_item)
            qurl = QUrl.fromEncoded(target_url)
            dataContent = str(responseItems[ResponsesTable.RES_DATA])

            # TODO: store reference
            fuzz_item = (fuzz_id, dataContent, qurl)
            self.qlock.unlock()
            locked = False

        finally:
            if locked:
                self.qlock.unlock()

        return fuzz_item

    def do_stopFuzzing(self):
        print('do_stopFuzzing')
        self.keep_fuzzing = False

    def generate_fuzz_values(self, response_id):

        row = self.Data.read_responses_by_id(self.read_cursor, response_id)
        if not row:
            self.framework.log_warning('missing response id: %s' % (response_id))
            return
        responseItems = [m or '' for m in row]

        url = str(responseItems[ResponsesTable.URL])
        contentType = str(responseItems[ResponsesTable.RES_CONTENT_TYPE])
        responseBody = str(responseItems[ResponsesTable.RES_DATA])

        # TODO: need better content type
        if 'html' not in contentType:
            if '<html' not in responseBody.lower():
                # non-html not supported
                self.framework.log_warning('skipping not HTML request for [%s]: %s' % (response_id, url))
                return 

        fuzz_payloads = self.calculate_fuzz_payloads(url)

        self.qlock.lock()
        try:
#             if self.fuzz_queue.has_key(url):
#                 # TODO: allow for better rescan in future
#                 self.framework.log_warning('adding already scanned url [%s] for now' % (url))

            for payload in fuzz_payloads:
                queue_item = [None, response_id, payload[0], payload[1], payload[2], payload[3], 'P']
                rowid = self.Data.add_dom_fuzzer_queue_item(
                    self.write_cursor, queue_item
                    )
                queue_item[0] = rowid
                self.queueDataModel.append_data([queue_item])
        finally:
            self.qlock.unlock()

    def do_populateExistingFuzzData(self):
        self.qlock.lock()
        try:
            rows = []
            for row in self.Data.get_dom_fuzzer_queue_items(self.read_cursor, 'P'):
                rows.append([m or '' for m in row])
            self.queueDataModel.append_data(rows)
            rows = []
            for row in self.Data.read_dom_fuzzer_results_info(self.read_cursor):
                rows.append([m or '' for m in row])
            self.resultsDataModel.append_data(rows)
        finally:
            self.qlock.unlock()

    def do_clearFuzzQueue(self):
        self.qlock.lock()
        try:
            self.Data.clear_dom_fuzzer_queue(self.write_cursor)
            self.queueDataModel.clearModel()
        finally:
            self.qlock.unlock()

    def calculate_fuzz_payloads(self, url):
        payloads = []
        splitted = urlparse.urlsplit(url)
        if not splitted.query:
            if not splitted.fragment:
                payloads.extend(self.calculate_fuzz_payload_tests(url+'?', 'url', ''))
                payloads.extend(self.calculate_fuzz_payload_tests(url+'#', 'url', ''))
            else:
                mangled = urlparse.urlunsplit((splitted.scheme, splitted.netloc, splitted.path, '', ''))
                mangled = '?#' + splitted.fragment
                payloads.extend(self.calculate_fuzz_payload_tests(mangled, 'url', ''))
        if splitted.query:
            payloads.extend(self.calculate_fuzz_payload_tests(url, 'query', splitted.query))
        if splitted.fragment:
            payloads.extend(self.calculate_fuzz_payload_tests(url, 'fragment', splitted.fragment))
        if splitted.query and not splitted.fragment:
            payloads.extend(self.calculate_fuzz_payload_tests(url, 'url', ''))
            mangled = urlparse.urlunsplit((splitted.scheme, splitted.netloc, splitted.path, '', splitted.query))
            payloads.extend(self.calculate_fuzz_payload_tests(mangled, 'fragment', splitted.query))
        return payloads

    def calculate_fuzz_payload_tests(self, url, target, url_field):

        payloads = []

        for test in self.STANDARD_TESTS:
            payloads.append((url, target, '', test))

        if url_field:
            pairs = self.re_delim.split(url_field)
            for test in self.STANDARD_TESTS:
                for offset in range(0, len(pairs)):
                    values = pairs[offset]
                    if values == ';' or values == '&':
                        continue
                    if '=' in values:
                        name, value = values.split('=', 1)
                    else:
                        name, value = values, ''
                    payloads.append((url, target, name, test))
                    
        return payloads


    def compute_url_from_payload(self, data_item):
        url = data_item[DomFuzzerQueueTable.URL]
        target = data_item[DomFuzzerQueueTable.TARGET]
        param = data_item[DomFuzzerQueueTable.PARAM]
        test = data_item[DomFuzzerQueueTable.TEST]

        if 'url' == target:
            if not param:
                return url + test
            else:
                # TODO: fix me
                return url + test + '=X'

        splitted = urlparse.urlsplit(url)
        if 'fragment' == target:
            url_field = splitted.fragment
        elif 'query' == target:
            url_field = splitted.query
        else:
            raise Exception('unsupported target: %s' % (target))

        if not url_field:
            pass
        else:
            # TODO: this duplicates previous work, so could consider pre-storing target urls?
            url_io = StringIO()
            pairs = self.re_delim.split(url_field)
            for offset in range(0, len(pairs)):
                values = pairs[offset]
                if values == ';' or values == '&':
                    url_io.write(values)
                    continue
                if '=' in values:
                    name, value = values.split('=', 1)
                    separator = '='
                else:
                    name, value = values, ''
                    separator = ''

                if name == param:
                    value += test

                url_io.write(name)
                url_io.write(separator)
                url_io.write(value)
                
        if 'fragment' == target:
            target_url = urlparse.urlunsplit((splitted.scheme, splitted.netloc, splitted.path, splitted.query, url_io.getvalue()))
        elif 'query' == target:
            target_url = urlparse.urlunsplit((splitted.scheme, splitted.netloc, splitted.path, url_io.getvalue(), splitted.fragment))

        return target_url

    def apply_fuzz_analysis(self, fuzz_id, fuzz_url, html, messages):
        # check higher confidence items first
        found = False
        confidence = ''
        for message in messages:
            if 'alert' == message[0] and message[2] in (self.NUM1, self.NUM2):
                found = True
                confidence = 'High'
    
        if not found:
            for test in self.STANDARD_TESTS:
                if test in html:
                    found = True
                    confidence = 'Medium'

        if not found:
            if self.re_unique_marker_base.search(html):
                confidence = 'Low'

        if found:
            fuzz_item = self.Data.get_dom_fuzzer_queue_item_by_id(self.read_cursor2, fuzz_id)
            if not fuzz_item:
                self.framework.log_warning('missing fuzz_id [%s]' % fuzz_id)
            else:
                flatten_url = str(fuzz_url.encode('ascii', 'ignore'))
                fuzz_results =  [None, fuzz_id, flatten_url, fuzz_item[DomFuzzerQueueTable.TARGET],
                     fuzz_item[DomFuzzerQueueTable.PARAM], fuzz_item[DomFuzzerQueueTable.TEST], confidence, html]
                rowid = self.Data.add_dom_fuzzer_results_item(self.write_cursor, fuzz_results)
                fuzz_results[0] = rowid
                self.resultsDataModel.append_data([fuzz_results])
