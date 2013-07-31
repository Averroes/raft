#
# Sequence manager for running sequences
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

from PyQt4.QtCore import (Qt, QObject, SIGNAL)
from core.database.constants import ResponsesTable, SequencesTable, SequenceStepsTable
from core.fuzzer.RequestInstance import RequestInstance

# TODO: get this out of utility and into extractors
from utility import ContentHelper

import uuid
import re

class SequenceManager(QObject):
    def __init__(self, framework, sequenceId, parent = None):
        QObject.__init__(self, parent)
        
        self.framework = framework
        self.sequenceId = sequenceId

        self.re_request = re.compile(r'^(\S+)\s+((?:https?://(?:\S+\.)+\w+(?::\d+)?)?/.*)\s+HTTP/\d+\.\d+\s*$', re.I)

        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.fill_sequence()

    def db_detach(self):
        self.close_cursor()
        self.Data = None
        self.sequenceId = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def fill_sequence(self):
        if not self.sequenceId:
            return

        dbrow = self.Data.get_sequence_by_id(self.cursor, self.sequenceId)
        items = [m or '' for m in dbrow]
        self.dynamic_data = bool(items[SequencesTable.DYNAMIC_DATA])
        if self.dynamic_data:
            raise Exception('dynamic sequences are not support currently')
        self.session_detection = bool(items[SequencesTable.SESSION_DETECTION])
        self.use_insession_re = bool(items[SequencesTable.INSESSION_RE])
        self.insession_pattern = str(items[SequencesTable.INSESSION_PATTERN])
        self.use_outofsession_re = bool(items[SequencesTable.OUTOFSESSION_RE])
        self.outofsession_pattern = str(items[SequencesTable.OUTOFSESSION_PATTERN])

        if self.use_insession_re:
            self.re_insession = re.compile(self.insession_pattern, re.I)
        else:
            self.insession_pattern = self.insession_pattern.lower()
        if self.use_outofsession_re:
            self.re_outofsession = re.compile(self.outofsession_pattern, re.I)
        else:
            self.outofsession_pattern = self.outofsession_pattern.lower()

        self.sequence_response_ids = []
        for row in self.Data.get_sequence_steps(self.cursor, self.sequenceId):
            items = [m or '' for m in row]
            if bool(items[SequenceStepsTable.IS_ENABLED]):
                self.sequence_response_ids.append(int(items[SequenceStepsTable.RESPONSE_ID]))

        self.request_instances = []
        for response_id in self.sequence_response_ids:
            row = self.Data.read_responses_by_id(self.cursor, response_id)
            response_item = [m or '' for m in row]
            url = str(response_item[ResponsesTable.URL])
            method = str(response_item[ResponsesTable.REQ_METHOD])
            headers = str(response_item[ResponsesTable.REQ_HEADERS])
            headers_dict = {}
            # TODO: this needs to be a framework method :(
            for line in headers.splitlines():
                if self.re_request.match(line):
                    continue
                elif ':' in line:
                    name, value = [v.strip() for v in line.split(':', 1)]
                    headers_dict[name] = value

            body = str(response_item[ResponsesTable.REQ_DATA])
            context = uuid.uuid4().hex

            request = RequestInstance(method, url, headers_dict, body, context, self)
            self.request_instances.append(request)

    def get_request_list(self):
        request_list = []
        for ri in self.request_instances:
            context = uuid.uuid4().hex
            request_list.append(RequestInstance(ri.method, ri.url, ri.headers, ri.body, context, self))
        return request_list

    def has_session_detection(self):
        return self.session_detection
        
    def analyze_response(self, response):
        # return Need Sequence, Run Again
        if not self.session_detection:
            return True, False

        is_insession = False
        is_outofsession = False

        charset = ContentHelper.getCharSet(response.content_type)
        responseHeaders, responseBody, rawResponse = ContentHelper.combineRaw(response.headers, response.body, charset)
        rawResponse_lower = ''

        if self.use_insession_re:
            if self.re_insession.search(rawResponse):
                is_insession = True
        elif self.insession_pattern:
            rawResponse_lower = rawResponse.lower()
            if -1 != rawResponse_lower.find(self.insession_pattern):
                is_insession = True

        if self.use_outofsession_re:
            if self.re_outofsession.search(rawResponse):
                is_outofsession = True
        elif self.outofsession_pattern:
            if '' == rawResponse_lower:
                rawResponse_lower = rawResponse.lower()
            if -1 != rawResponse_lower.find(self.outofsession_pattern):
                is_outofsession = True

        if is_insession and not is_outofsession:
            return False, False
        elif not is_insession and is_outofsession:
            return True, True
        elif not is_insession and not is_outofsession:
            return False, False
        else:
            # conflicted, so run sequence, but not item
            return True, False
        
