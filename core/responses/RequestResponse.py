#
# This module supports the parsing and objectification of the HTTP Request/Response
#
# Authors: 
#          Seth Law (seth.w.law@gmail.com)
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
from utility import ContentHelper

class RequestResponse(object):
    def __init__(self, framework):
        self._framework = framework
        self._results = None
        self._requestParams = None
        self._combinedRequest = False
        self._combinedResponse = False
        self._requestUTF8Headers = None
        self._requestUTF8Body = None
        self._rawRequest = None
        self._responseUTF8Headers = None
        self._responseUTF8Body = None
        self._rawResponse = None

        ######
        self.Id = ''
        self.requestHeaders = b''
        self.requestBody = b''
        self.requestHost = ''
        self.requestHash = ''
        self.requestDate = ''
        self.requestTime = ''
        self.responseHeaders = b''
        self.responseBody = b''
        self.responseStatus = ''
        self.responseHash = ''
        self.responseContentType = ''
        self.notes = ''
        self.confirmed = ''

        self.contentType = ''
        self.charset = ''
        self.baseType = ''
        ######

    @property
    def results(self):
        """ Get the extracted data results"""
        if self._results is not None:
            return self._results

        if 'html' == self.baseType:
            self._results = self._framework.getContentExtractor().getExtractor('html').process(self.responseBody, self.responseUrl, self.charset, None)
        elif 'javascript' == self.baseType:
            self._results = self._framework.getContentExtractor().getExtractor('javascript').process(self.responseUTF8Body, self.responseUrl, self.charset, None)
        else:
            # TODO: implement more types
            self._results = None
            pass

        return self._results

    @property
    def requestParams(self):
        """ Get a Dictionary containing all request parameters """
        if self._requestParams is not None:
            return self._requestParams

        self._requestParams = {}
        # extract request parameters
        # TODO: repeated parameters clobber earlier values
        # TODO: this should be processed when needed, not everytime
        splitted = urlparse.urlsplit(self.responseUrl)
        if splitted.query:
            qs_values = urlparse.parse_qs(splitted.query, True, errors='ignore')
            for name, value in qs_values.items():
                self._requestParams[name] = value
        postDataResults = self._framework.getContentExtractor().getExtractor('post-data').process_request(self.requestHeaders, self.requestBody)
        if postDataResults:
            # TODO: support non-name/value pair types
            for name, value in postDataResults.name_values_dictionary.items():
                # XXX: bytes
                self._requestParams[name] = value

        return self._requestParams

        
    @property
    def requestUTF8Headers(self):
        """ Get the request headers as a UTF-8 string """
        if not self._combinedRequest:
            self._doCombineRequest()
        return self._requestUTF8Headers

    @property
    def requestUTF8Body(self):
        """ Get the request body as a UTF-8 string """
        if not self._combinedRequest:
            self._doCombineRequest()
        return self._requestUTF8Body

    @property
    def rawRequest(self):
        """ Get a representation of the raw request """
        if not self._combinedRequest:
            self._doCombineRequest()
        return self._rawRequest

    @property
    def responseUTF8Headers(self):
        """ Get the response headers as a UTF-8 string """
        if not self._combinedResponse:
            self._doCombineResponse()
        return self._responseUTF8Headers

    @property
    def responseUTF8Body(self):
        """ Get the response body as a UTF-8 string """
        if not self._combinedResponse:
            self._doCombineResponse()
        return self._responseUTF8Body

    @property
    def rawResponse(self):
        """ Get a representation of the raw response """
        if not self._combinedResponse:
            self._doCombineResponse()
        return self._rawResponse


    def _doCombineRequest(self):
        self._requestUTF8Headers, self._requestUTF8Body, self._rawRequest = ContentHelper.combineRaw(self.requestHeaders, self.requestBody)
        self._combinedRequest = True

    def _doCombineResponse(self):
        self._responseUTF8Headers, self._responseUTF8Body, self._rawResponse = ContentHelper.combineRaw(self.responseHeaders, self.responseBody, self.charset)
        self._combinedResponse = True

