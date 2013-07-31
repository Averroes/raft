#
# Author: Nathan Hamiel
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
#!/usr/bin/env python

import urllib2
import datetime
from keepalive import HTTPHandler
from keepalive import HTTPSHandler

from PyQt4.QtCore import (Qt, SIGNAL, QUrl, QTimer, QObject, QVariant)
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *

METHODS = """GET
POST
PUT
DELETE
HEAD
TRACE
TRACK
OPTIONS
CONNECT
PROPFIND
PROPPATCH
MKCOL
COPY
MOVE
LOCK
UNLOCK"""

def from_request_tool(host, port, url, body, secure):
        """ Construct a proper request object to be sent to the request handler. Request items should
        be pretty cleaned up by the time they are passed to this function. """
        # ToDo: All of this is a work in progress. Obviously not an exact science.
        
        if secure:
            fullurl = "https://{0}:{1}{2}".format(host, port, url)
        else:
            fullurl = "http://{0}:{1}{2}".format(host, port, url)
        
        bodyContent = body.split("\n")
        requestLine = ""
        method = ""
        # Grab the request line
        firstLine = bodyContent[0]
        for item in METHODS.splitlines():
            if item in firstLine[0:10]:
                method = item        
                requestLine = bodyContent[0]
        
        # Remove the requestLine and add a new list
        bodyContent.remove(requestLine)
        remains = list(bodyContent)
        
        # Format headers in a Python dictionary
        headers = {}
        for item in bodyContent:
            if item == "":
                break
            values = item.split(":")
            headers[values[0]] = values[1]
            remains.remove(item)
            
        if headers == {}:
            headers = None
        
        # Now grab the data left from the request
        data = ""
        for item in remains:
            if item == "":
                pass
            data += item
        
        if data == "":
            data = None
        
        # Send data to requester object
        requesterResponse = Requester(fullurl, method, data, headers)
                
        # Format the response data to return to the Requester tool
        respHeaders = requesterResponse[0]
        # response headers
        formatHeaders = ""
        for key in respHeaders:
            formatHeaders += "{0}: {1}\n".format(key, respHeaders[key])
            
        # content
        content = requesterResponse[1]
        # code
        code = requesterResponse[2]
        # time
        time = requesterResponse[3]
        
        # Return a RAFT object to the caller: url, request headers, request data, response headers,
        # response content, response code, time request took.
        return(fullurl, headers, data, formatHeaders.rstrip(), content, code, time)
            
def Requester(url, method="GET", postdata=None, headers=None):
    """ The main request function. Request data should be properly cleaned by the time they get to
    this function. Reimplements the Request class and adds support for handlers. Function
    must specifify a URL as well as optional request method, postdata, and headers """
    
    #ToDo: In the future ensure that the class is initialized with any custom openers 
    Req = Request()
    
    response = Req.fetch(url, method, postdata, headers)
    return(response)
    

class Request:
    """ A class for creating HTTP and HTTPS requests """
    def __init__(self):
        # Create a custom opener that supports keepalives on HTTP and HTTPS
        customOpener = urllib2.build_opener(HTTPHandler(), HTTPSHandler())
        urllib2.install_opener(customOpener)
        
    def fetch(self, location, method="GET", postdata=None, headers=None):
        """ This provides a convenience function for making requests. This interfaces
        with urllib2 and provides the ability to make GET, POST, PUT and DELETE requests.
        The return data from this function is headers, content, http status, and
        the timedelta from a succesful request"""
        
        # Checks to ensure that header values and postdata are in the appropriate format
        if type(headers) != dict and headers != None:
            raise TypeError, ("headers are not a valid Python dictionary")
        if type(postdata) != str and postdata != None:
            raise TypeError, ("postdata is not a valid Python string")
        
        if headers:
            req = urllib2.Request(location, method, headers=headers)
        else:
            req = urllib2.Request(location, method)
            
        req.get_method = lambda: method.upper()
        req.add_data(postdata)
        
        # Anticipate errors from either unavailable content or nonexistent resources
        try:
            start = datetime.datetime.now()
            response = urllib2.urlopen(req)
            end = datetime.datetime.now()
        except urllib2.HTTPError, error:
            return(error.headers, error.read(), error.code, None)
        except urllib2.URLError, error:
            # Noneexistent resources won't have headers or status codes
            return(None, error.reason, None, None)
        else:
            headers = response.info()
            content = response.read()
            # Grab the HTTP Status Code
            code = response.getcode()
            # Compute timedelta from a successful request
            time = end - start
            return(headers, content, code, time)
            
class Req:
        """ A class for requesting resources from the web """
        
        def __init__(self, jar=None):
                
                self.manager = QNetworkAccessManager()
                self.request = QNetworkRequest()
                
                if jar:
                        self.manager.setCookieJar(jar)
                        
        
        def from_request_tool(self, host, port, url, body, secure):
                """ Construct a proper request object to be sent to the request handler. Request items should
                be pretty cleaned up by the time they are passed to this function. """
                # ToDo: All of this is a work in progress. Obviously not an exact science.
                
                
                if secure:
                    fullurl = "https://{0}:{1}{2}".format(host, port, url)
                else:
                    fullurl = "http://{0}:{1}{2}".format(host, port, url)
                    
                self.request.setUrl(QUrl(fullurl))
                
                bodyContent = body.split("\n")
                requestLine = ""
                method = ""
                # Grab the request line
                firstLine = bodyContent[0]
                for item in METHODS.splitlines():
                    if item in firstLine[0:10]:
                        method = item        
                        requestLine = bodyContent[0]
                
                # Remove the requestLine and add a new list
                bodyContent.remove(requestLine)
                remains = list(bodyContent)
                
                # Format headers in a Python dictionary
                headers = {}
                for item in bodyContent:
                    if item == "":
                        break
                    values = item.split(":")
                    headers[values[0]] = values[1]
                    self.request.setRawHeader(values[0], values[1])
                    remains.remove(item)
                    
                if headers == {}:
                    headers = None
                
                # Now grab the data left from the request
                data = ""
                for item in remains:
                    if item == "":
                        pass
                    data += item
                
                if data == "":
                    data = None
                
                # Send data to requester object
                requesterResponse = Requester(fullurl, method, data, headers)
 
                if method == "GET":
                        self.reply = self.manager.get(self.request)
                        self.reply.finished.connect(self.run_finished)
                elif method == "POST":
                        pass
                else:
                        print("Method not supported")
                        
                
                        
                # Format the response data to return to the Requester tool
                respHeaders = requesterResponse[0]
                # response headers
                formatHeaders = ""
                for key in respHeaders:
                    formatHeaders += "{0}: {1}\n".format(key, respHeaders[key])
                    
                # content
                content = requesterResponse[1]
                # code
                code = requesterResponse[2]
                # time
                time = requesterResponse[3]
                
                # Return a RAFT object to the caller: url, request headers, request data, response headers,
                # response content, response code, time request took.
                return(fullurl, headers, data, formatHeaders.rstrip(), content, code, time)
                
        def run_finished(self):
                """ Run when the request is finished """
                print("Fuck yea")
                data = self.reply.readAll()
                print(data)
                        
                
        
