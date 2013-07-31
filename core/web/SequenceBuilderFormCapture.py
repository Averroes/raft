#
# Form capture for sequence building
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

from PyQt4.QtCore import (Qt, SIGNAL, QObject, QMutex)

from urllib import parse as urlparse

class SequenceParameter():
    def __init__(self, url, source, name, Type, position):
        self.url = url
        self.source = source
        self.name = name
        self.Type = Type
        self.position = position
        self.hashval = ('\x01'.join((source, name, Type, str(position)))).__hash__()

    def __repr__(self):
        return ('SequenceParameter(%s, %s, %s, %s, %s)' % (repr(self.url), repr(self.source), repr(self.name), repr(self.Type), self.position))
    
    def __eq__(self, other):
        return (self.source == other.source) and (self.name == other.name) and (self.Type == other.Type) and (self.position == other.position)

    def __hash__(self):
        # TODO: fixme
        return self.hashval
    
class SequenceBuilderFormCapture(QObject):
    def __init__(self, framework, parent = None):
        QObject.__init__(self, parent)
        self.framework = framework
        self.targets = {}
        self.source_urls = {}
        self.source_parameters = {}
        self.target_parameters = {}
        self.sequence_transitions = {}
        self.is_tracking = False

        self.qlock = QMutex()

        self.postDataExtractor = self.framework.getContentExtractor().getExtractor('post-data')

    def set_source_url(self, request_id, url):
        if not self.is_tracking:
            return
        self.qlock.lock()
        try:
            request_id = str(request_id)

            self.source_urls[request_id] = url
            if request_id not in self.source_parameters:
                self.source_parameters[request_id] = {}

            self.source_parameters[request_id] = self.process_url(url, self.source_parameters[request_id])
        finally:
            self.qlock.unlock()

    def process_url(self, url, parameters):
        splitted = urlparse.urlsplit(url)
        if splitted.query:
            qs_values = urlparse.parse_qs(splitted.query, True)
            position = 0
            for name, value in qs_values.items():
                position += 1
                parameters[SequenceParameter(url, 'Query', name, '', position)] = value
        if splitted.fragment:
            qs_values = urlparse.parse_qs(splitted.fragment, True)
            position = 0
            for name, value in qs_values.items():
                position += 1
                parameters[SequenceParameter(url, 'Fragment', name, '', position)] = value

        return parameters

    def store_source_parameter(self, request_id, position, name, Type, value):
        if not self.is_tracking:
            return
        self.qlock.lock()
        try:
            request_id = str(request_id)
            url = self.source_urls[request_id]
            sequenceParameter = SequenceParameter(url, 'Form', name, Type, position)
            self.source_parameters[request_id][sequenceParameter] = [value]
        finally:
            self.qlock.unlock()
        
    def process_target_request(self, response_id, originating_request_id, method, url, request_headers, request_body):
        if not self.is_tracking:
            return
        self.qlock.lock()
        try:
            response_id = str(response_id)
            originating_request_id = str(originating_request_id)

            self.targets[response_id] = originating_request_id

            if response_id not in self.target_parameters:
                self.target_parameters[response_id] = {}

            self.target_parameters[response_id] = self.process_url(url, self.target_parameters[response_id])

            results = self.postDataExtractor.process_request(request_headers, request_body)
            if results:
                position = 0
                # TODO: support non-name/value pair types
                for name, value, Type in results.name_values:
                    position += 1
                    self.target_parameters[response_id][SequenceParameter(url, method, name, Type, position)] = value
        finally:
            self.qlock.unlock()

    def start_tracking(self):
        self.is_tracking = True

    def stop_tracking(self):
        self.is_tracking = False

    def set_sequence_transition(self, requestId, originatingResponseId, previousRequestId):
        if not self.is_tracking:
            return
        self.qlock.lock()
        try:
            print(('transition sequence; requestId=%s, originatingResponseId=%s, prev=%s' % (requestId, originatingResponseId, previousRequestId)))
            self.sequence_transitions[requestId] = originatingResponseId
            if previousRequestId in self.source_parameters:
                if requestId not in self.source_parameters:
                    self.source_parameters[requestId] = {}
                parameters = self.source_parameters[requestId]
                for param, value in self.source_parameters[previousRequestId].items():
                    parameters[param] = value
            if previousRequestId in self.source_urls:
                self.source_urls[requestId] = self.source_urls[previousRequestId]
        finally:
            self.qlock.unlock()

    def get_sequence_transition(self, requestId):
        if requestId in self.sequence_transitions:
            return str(self.sequence_transitions[requestId])
        else:
            return ''

    def allParameters(self, response_ids):

#        print(self.source_parameters)

        response_ids = [str(m) for m in response_ids]
        response_ids.sort()

        parameters = []
        source_parameters_for_response = {}

        print(('targets', self.targets))

        for response_id in response_ids:
            request_id = self.targets.get(response_id)
            if request_id and request_id in self.source_parameters:
                # TODO: FIX THIS properly!
                # source parameters can be collected multiple times
                if response_id not in source_parameters_for_response:
                    source_parameters_for_response[response_id] = {}
                parameters_for_response = source_parameters_for_response[response_id]
                for param, values in self.source_parameters[request_id].items():
                    if param not in parameters_for_response:
                        parameters_for_response[param] = values

        for response_id in response_ids:
            if response_id in self.target_parameters:
                if response_id in source_parameters_for_response:
                    for param, values in source_parameters_for_response[response_id].items():
                        responseId = self.get_sequence_transition(request_id)
                        parameters.append((responseId, request_id, param, values, 'source'))
                request_id = self.targets.get(response_id)
                for param, values in self.target_parameters[response_id].items():
                    parameters.append((response_id, request_id, param, values, 'target'))

        return parameters
