#
# request runner
#
# Authors: 
#          Gregory Fleischer (gfleischer@gmail.com)
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

from PyQt4.QtCore import (Qt, QObject, SIGNAL, QMutex)

from core.network.StandardNetworkAccessManager import StandardNetworkAccessManager
from core.network.InMemoryCookieJar import InMemoryCookieJar
from core.network.NetworkRequester import NetworkRequester
from core.fuzzer.RequestInstance import RequestInstance
from core.fuzzer.SequenceManager import SequenceManager

import collections
import uuid

class RequestRunner(QObject):

    def __init__(self, framework, parent = None):
        QObject.__init__(self, parent)

        self.framework = framework

        self.request_queue = None

        self.qlock = QMutex()
        self.cookieJar = None
        self.networkRequester = None
        self.networkAccessManager = None
        self.sequenceManager = None
        self.postSequenceManager = None

        self.request_queue = collections.deque()
        self.request_context = {}

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

        self.max_concurrent = 10

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def setup(self, callback, cookieJar, sequenceId = None, postSequenceId = None):

        QObject.connect(self, SIGNAL('requestFinished(int, QString)'), callback, Qt.DirectConnection) 

        self.sequence_enabled = False
        self.sequence_needed = False
        self.post_sequence_enabled = False
        if sequenceId:
            self.sequenceManager = SequenceManager(self.framework, sequenceId, self)
            self.sequence_enabled = True
            self.sequence_needed = True
        if postSequenceId:
            self.postSequenceManager = SequenceManager(self.framework, postSequenceId, self)
            self.post_sequence_enabled = True

        self.cookieJar = cookieJar

        self.networkAccessManager = StandardNetworkAccessManager(self.framework, self.cookieJar)
        self.networkRequester = NetworkRequester(self.framework, self.networkAccessManager, self.response_received, self)

        self.inflight_list = {}

    def queue_request(self, method, url, headers, body, context = ''):
        if not context:
            context = uuid.uuid4().hex

        request = RequestInstance(method, url, headers, body, context, self)

        do_process = False

        self.qlock.lock()
        try:
            if self.sequence_needed:
                self.setup_sequence_items()
                self.sequence_needed = False

            self.request_context[request.context] = request
            self.request_queue.append(request)

            if 0 == len(self.inflight_list):
                do_process = True
            elif (self.sequence_enabled or self.post_sequence_enabled): # TODO: this needs to modified to detect when a sequence is being run
                do_process = False
            elif len(self.inflight_list) < self.max_concurrent:
                do_process = True

        finally:
            self.qlock.unlock()

        if do_process:
            self.process_next()

        return request

    def response_received(self, response):
        do_process = False
        user_request_completed = False
        is_sequence = False
        original_request = None
        self.qlock.lock()
        try:
            if not self.inflight_list.has_key(response.context):
                raise Exception('unexpected response; context=%s' % (response.context))
            request = self.inflight_list.pop(response.context)

            if self.request_context.has_key(response.context):
                # user request
                if not self.sequence_enabled:
                    user_request_completed = True
                    self.request_context.pop(response.context)
                else:
                    original_request = self.request_context[response.context]
                    user_request_completed = True
                    need_sequence, run_again = self.sequenceManager.analyze_response(response)
                    if need_sequence:
                        original_request.sequence_needed = True
                    if run_again:
                        self.request_queue.appendleft(original_request)
                        user_request_completed = False
                    else:
                        self.request_context.pop(response.context)

                if user_request_completed:
                    if self.post_sequence_enabled:
                        self.setup_post_sequence_items()
            else:
                is_sequence = True

            if 0 == len(self.inflight_list):
                do_process = True
            elif is_sequence:
                do_process = False
            elif self.sequence_enabled and not self.sequenceManager.has_session_detection():
                do_process = False
            elif len(self.inflight_list) < self.max_concurrent:
                do_process = True

        finally:
            self.qlock.unlock()

        if user_request_completed:
            self.emit(SIGNAL('requestFinished(int, QString)'), response.response_id, response.context)

        if do_process:
            self.process_next()

    def process_next(self):
        is_locked = False
        try:
            keep_looping = True
            while keep_looping:

                self.qlock.lock()
                is_locked = True

                if len(self.request_queue) == 0:
                    break

                if self.sequence_enabled and not self.sequenceManager.has_session_detection():
                    single_step = True
                elif  self.post_sequence_enabled:
                    single_step = True
                else:
                    single_step = False

                request = self.request_queue.popleft()
                if self.request_context.has_key(request.context):
                    if self.sequence_enabled and request.sequence_needed:
                        single_step = True
                        # put back user request
                        request.sequence_needed = False
                        self.request_queue.appendleft(request)
                        self.setup_sequence_items()
                        request = self.request_queue.popleft()
                else:
                    single_step = True

                self.inflight_list[request.context] = self.networkRequester.send(
                    request.method, request.url, request.headers, request.body, request.context
                    )
                if single_step or len(self.inflight_list) >= self.max_concurrent:
                    keep_looping = False
                
                self.qlock.unlock()
                is_locked = False
                
        finally:
            if is_locked:
                self.qlock.unlock()
        
    def setup_sequence_items(self):
        # this function must be called with lock
        request_list = self.sequenceManager.get_request_list()
        for i in range(len(request_list), 0, -1):
            request = request_list[i-1]
            self.request_queue.appendleft(request)

    def setup_post_sequence_items(self):
        # this function must be called with lock
        request_list = self.postSequenceManager.get_request_list()
        for i in range(len(request_list), 0, -1):
            self.request_queue.appendleft(request_list[i-1])
