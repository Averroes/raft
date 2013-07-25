#!/usr/bin/env python
#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2011-2013 RAFT Team
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

from xml.sax.saxutils import escape
from urllib import parse as urlparse
import sys, logging, os, time, collections
import lzma
import re
import traceback
import io
import base64

#### from PyQt4.QtCore import QTimer, SIGNAL, SLOT, QUrl, QObject, QIODevice, QThread
import PyQt4

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from PyQt4 import QtWebKit, QtNetwork

try:
    QUrl.FullyEncoded
except AttributeError:
    QUrl.FullyEncoded = QUrl.FormattingOptions(0x100000 | 0x200000 | 0x400000 | 0x800000 | 0x1000000)

MAX_LINK_COUNT = 100

class CookieJar(QtNetwork.QNetworkCookieJar):
    def __init__(self, parent = None):
        QtNetwork.QNetworkCookieJar.__init__(self, parent)
    def cookiesForUrl(self, url):
        cookieList = QtNetwork.QNetworkCookieJar.cookiesForUrl(self, url)
        if False:
            print(('get cookie url= %s' % (url.toString(QUrl.FullyEncoded))))
            for cookie in cookieList:
                print(('  Cookie: %s' % (cookie.toRawForm(QtNetwork.QNetworkCookie.Full))))
        return cookieList

    def setCookiesFromUrl(self, cookieList, url):
        if False:
            print(('set cookie url= %s' % (url.toString(QUrl.FullyEncoded))))
            for cookie in cookieList:
                print(('  Set-Cookie: %s' % (cookie.toRawForm(QtNetwork.QNetworkCookie.Full))))
        ok = QtNetwork.QNetworkCookieJar.setCookiesFromUrl(self, cookieList, url)
        return ok

class WrapIODevice(QIODevice):
    def __init__(self, ioDevice):
        QIODevice.__init__(self, ioDevice)
        self.ioDevice = ioDevice
        self.__data = ''

        # TODO: review QBuffer implementation -- these may be unneeded
        QObject.connect(self.ioDevice, SIGNAL('readChannelFinished()'), self.handleReadChannelFinished)
        QObject.connect(self.ioDevice, SIGNAL('readyRead()'), self.handleReadyRead)
        QObject.connect(self.ioDevice, SIGNAL('aboutToClose()'), self.handleAboutToClose)

        self.open(self.ReadOnly)
        self.setOpenMode(self.ioDevice.openMode())

    def handleAboutToClose(self):
        self.emit(SIGNAL("aboutToClose()"))

    def handleReadyRead(self):
        self.emit(SIGNAL("readyRead()"))

    def handleReadChannelFinished(self):
        self.emit(SIGNAL("readChannelFinished()"))

    def getdata(self):
        return self.__data

    def __getattr__(self, name):
        ret = getattr(self.ioDevice, name)
        return ret

    def abort(self):
        self.ioDevice.abort()

    def isSequential(self):
        return self.ioDevice.isSequential()

    def bytesAvailable(self):
        return self.ioDevice.bytesAvailable()

    def readData(self, maxSize):
        data = self.ioDevice.read(maxSize)
        if data:
            self.__data += data
        return data.data()
        
class NetworkReply(QtNetwork.QNetworkReply):
    def __init__(self, networkAccessManager, writer, request, outgoingData, reply):
        QtNetwork.QNetworkReply.__init__(self, reply)
        self.__networkAccessManager = networkAccessManager
        self.__writer = writer
        self.__setupRequestAndReply(request, outgoingData, reply)
        self.__finished = False
        self.open(self.ReadOnly | self.Unbuffered)

    def __setupRequestAndReply(self, request, outgoingData, reply):
        self.__request = request
        self.__outgoingData = outgoingData
        self.__reply = reply
        self.__data = b''
        self.__datalen = 0
        self.__offset = 0
        self.__datetime = time.time()

        QObject.connect(self.__reply, SIGNAL('sslErrors(const QList<QSslError> &)'), self.handleSslErrors)
        QObject.connect(self.__reply, SIGNAL('error(QNetworkReply::NetworkError)'), self.handleError)
        QObject.connect(self.__reply, SIGNAL('finished()'), self.handleFinished)

        self.setUrl(self.__request.url())

    def __getOperationString(self):
        op = self.__reply.operation()
        if QtNetwork.QNetworkAccessManager.HeadOperation == op:
            return 'HEAD'
        elif QtNetwork.QNetworkAccessManager.GetOperation == op:
            return 'GET'
        elif QtNetwork.QNetworkAccessManager.PutOperation == op:
            return 'PUT'
        elif QtNetwork.QNetworkAccessManager.PostOperation == op:
            return 'POST'
        elif QtNetwork.QNetworkAccessManager.DeleteOperation == op:
            return 'DELETE'
        else:
            # CUSTOM
            return self.__request.attribute(self.__request.CustomVerbAttribute).data().decode('ascii')
        
    def handleError(self, error):
        print(('error: ', error))

    def handleSslErrors(self, errorList):
        try:
            for error in errorList:
                print(error)
            self.__reply.ignoreSslErrors()
        except Exception as e:
            print(('Failed: %s' % (traceback.format_exc(e))))

    def handleFinished(self):
        request = self.__request
        reply = self.__reply

        responseData = reply.readAll()
        self.__data = responseData.data()
        self.__datalen = len(self.__data)
        self.__offset = 0

        status = reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute)
        fromCache = bool(reply.attribute(QtNetwork.QNetworkRequest.SourceIsFromCacheAttribute))

        qurl = self.__request.url()
        # Qt 5 => url = qurl.toDisplayString()
#        url = qurl.toEncoded().data().decode('utf-8')
        url = qurl.toString(QUrl.FullyEncoded)
        if not status or fromCache or url.startswith('about:') or url.startswith('data:'):
            pass
        else:
            self.__writeData(request, reply, status, self.__data)

        # check for redirect
        redirectTarget = reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute)
        if False and redirectTarget:
            targetUrl = redirectTarget.toUrl()
            if not targetUrl.isEmpty():
                if targetUrl.isRelative():
                    targetUrl = reply.url().resolved(targetUrl)
                # simple redirect policy
                if targetUrl != reply.url():
                    originatingObject = reply.request().originatingObject()
                    if not originatingObject or (reply.url() != originatingObject.requestedUrl()):
                        userAgent = request.rawHeader('User-Agent')
#                        print('reply finished: %s, direct to redirect target=%s' % (reply.url().toString(), targetUrl.toString()))
                        self.__request.setUrl(targetUrl)
                        redirectRequest = QtNetwork.QNetworkRequest(targetUrl)
                        redirectRequest.setRawHeader('User-Agent', userAgent)
                        redirectReply = self.__networkAccessManager.get(redirectRequest)
                        self.__setupRequestAndReply(redirectRequest, None, redirectReply)
                        return

        # set headers in response and signal finished
        for bname in reply.rawHeaderList():
            bvalue = reply.rawHeader(bname)
            self.setRawHeader(bname, bvalue)

        contentType = reply.header(QtNetwork.QNetworkRequest.ContentTypeHeader)
        if not contentType:
            # TODO: implement real "sniff" content-type
            if -1 != self.__data.find(b'<html'):
                contentType = 'text/html'
                self.setRawHeader('Content-Type', contentType.encode('utf-8'))
                reply.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, contentType)

        self.__finished = True
        self.emit(SIGNAL("readyRead()"))
        self.emit(SIGNAL('finished()'))
    
    def __writeData(self, request, reply, status, responseData):
        outgoingData = self.__outgoingData
        method = self.__getOperationString()
        url = request.url().toString(QUrl.FullyEncoded)
        parsed = urlparse.urlsplit(url)
        relativeUrl = urlparse.urlunsplit(('','', parsed.path, parsed.query, ''))
        host = parsed.hostname

        bio = io.BytesIO()
        bio.write(method.encode('ascii'))
        bio.write(b' ')
        bio.write(relativeUrl.encode('utf-8'))
        bio.write(b' HTTP/1.1\r\n')
        for bname in request.rawHeaderList():
            bvalue = request.rawHeader(bname)
            name = bname.data()
            value = bvalue.data()
            if b'host' == name.lower():
                host = value.encode('utf-8')
            bio.write(name)
            bio.write(b': ')
            bio.write(value)
            bio.write(b'\r\n')
        bio.write(b'\r\n')
        requestHeaders = bio.getvalue()

        contentType = reply.header(QtNetwork.QNetworkRequest.ContentTypeHeader)
        contentLength = reply.header(QtNetwork.QNetworkRequest.ContentLengthHeader)
        if contentLength is None:
            contentLength = len(responseData)
        else:
            contentLength = int(contentLength)

        status = str(status)
        msg = self.__reply.attribute(QtNetwork.QNetworkRequest.HttpReasonPhraseAttribute)
        bio = io.BytesIO()
        bio.write(b'HTTP/1.1 ')
        bio.write(status.encode('ascii'))
        bio.write(b' ')
        bio.write(msg.encode('utf-8'))
        bio.write(b'\r\n')
        for bname in reply.rawHeaderList():
            bvalue = reply.rawHeader(bname)
            bio.write(bname.data())
            bio.write(b': ')
            bio.write(bvalue.data())
            bio.write(b'\r\n')
        bio.write(b'\r\n')
        responseHeaders = bio.getvalue()

        requestData = b''
        if outgoingData:
            requestData = outgoingData.getdata()

        data = (
            method,
            url,
            host,
            self.__datetime,
            requestHeaders,
            requestData,
            status,
            int((time.time() - self.__datetime)*1000),
            contentType,
            contentLength,
            responseHeaders,
            responseData
            )
        self.__writer.write(data)

    def request(self):
        return self.__request

    def operation(self):
        return self.__reply.operation()

    def attribute(self, code):
        return self.__reply.attribute(code)

    def header(self, code):
        return self.__reply.header(code)

    def isFinished(self):
        return self.__finished

    def isRunning(self):
        return not self.__finished

    # from QIODevice

    def abort(self):
        pass

    def isSequential(self):
        return True

    def bytesAvailable(self):
        ba = self.__datalen - self.__offset
        return ba

    def readData(self, maxSize):
        size = min(self.__datalen - self.__offset, maxSize)
        if size <= 0:
            return b''
        data = self.__data[self.__offset:self.__offset+size]
        self.__offset += size
        return data

class NetworkMemoryCache(QtNetwork.QAbstractNetworkCache):
    def __init__(self, parent = None):
        QtNetwork.QAbstractNetworkCache.__init__(self, parent)
        self.size = 0
        self.cache = {} # list of [metaData, device] entries by url
        self.outstanding = {}
    
    def cacheSize(self):
        return self.size

    def clear(self):
        for k in list(self.cache.keys()):
            metaData, buf, mtime = self.cache.pop(k)
            if buf:
                self.size -= buf.length()
                buf.clear()
            metaData, buf = None, None            

    def data(self, url):
        k = url.toString(QUrl.FullyEncoded)
        if k in self.cache:
            buf = self.cache[k][1]
            device = QBuffer(buf)
            device.open(QIODevice.ReadOnly|QIODevice.Unbuffered)
            return device
        return None

    def insert(self, device):
        for k in list(self.outstanding.keys()):
            if self.outstanding[k] == device:
                self.size += device.size()
                self.cache[k][1] = device.data()
                device = None
                return
        else:
            raise Exception('Failed to find outstanding entry on cache insert')

    def metaData(self, url):
        k = url.toString(QUrl.FullyEncoded)
        if k in self.cache:
            metaData, buf, mtime = self.cache.pop(k)
            if buf:
                return metaData
        # return non-valid
        metaData = QtNetwork.QNetworkCacheMetaData()
        return metaData

    def prepare(self, metaData):
        k = metaData.url().toString(QUrl.FullyEncoded)
        self.cache[k] = [metaData, None, time.time()]
        device = QBuffer()
        device.open(QIODevice.ReadWrite|QIODevice.Unbuffered)
        self.outstanding[k] = device
        return device

    def remove(self, url):
        k = url.toString(QUrl.FullyEncoded)
        if k in self.outstanding:
            device = self.outstanding.pop(k)
            device = None
        if k in self.cache:
            metaData, buf, mtime = self.cache.pop(k)
            if buf:
                self.size -= buf.length()
                buf.clear()
            metaData, buf = None, None
        return False

    def updateMetaData(self, metaData):
        url = metaData.url().toString(QUrl.FullyEncoded)
        if url in self.cache:
            self.cache[url][0] = metaData

class NetworkCacheL(QtNetwork.QAbstractNetworkCache):
    def __init__(self, parent = None):
        QtNetwork.QAbstractNetworkCache.__init__(self, parent)

        if False:
            self.__cachedir = '.raftcache'
            if not os.path.exists(self.__cachedir):
                os.mkdir(self.__cachedir)
            self.__cache = QtNetwork.QNetworkDiskCache()
            self.__cache.setCacheDirectory(self.__cachedir)

    #        self.nc = self.__cache
        else:
            self.nc = NetworkMemoryCache(parent)

    def __attr__(self, name):
        ###print(('NetworkCache: [%s]' % (name)))
        return getattr(self.nc, msg)

    def insert(self, device):
        msg = 'NetworkCache: [%s](%s)' % ('insert', device)
        r = self.nc.insert(device)
        ###print(('%s -> %s' % (msg, r)))
        return r

    def metaData(self, url):
        msg = 'NetworkCache: [%s](%s)' % ('metaData', url)
        r = self.nc.metaData(url)
        ###print(('%s -> %s, isValid=%s' % (msg, r, r.isValid())))
        ###print(('\n'.join(['%s: %s' % (n, v) for n,v in r.rawHeaders()])))
        return r

    def data(self, url):
        msg = 'NetworkCache: [%s](%s)' % ('data', url)
        r = self.nc.data(url)
        if r:
            print(('%s -> %s, isOpen=%s' % (msg, r, r.isOpen())))
        return r

    def prepare(self, metaData):
        msg = 'NetworkCache: [%s](%s)' % ('prepare', metaData)
        r = self.nc.prepare(metaData)
        ###print(('%s -> %s' % (msg, r)))
#        print('\n'.join(['%s: %s' % (n, v) for n,v in metaData.rawHeaders()]))
        return r

    def remove(self, url):
        msg = 'NetworkCache: [%s](%s)' % ('remove', url)
        r = self.nc.remove(url)
        ###print(('%s -> %s' % (msg, r)))
        return r

    def updateMetaData(self, metaData):
        msg = 'NetworkCache: [%s](%s)' % ('updateMetaData', metaData)
        r = self.nc.updateMetaData(metaData)
        ###print(('%s -> %s' % (msg, r)))
        ###print(('\n'.join(['%s: %s' % (n, v) for n,v in metaData.rawHeaders()])))

class NetworkManager(QtNetwork.QNetworkAccessManager):
    def __init__(self, writer, parent = None):
        QtNetwork.QNetworkAccessManager.__init__(self, parent)
        self.writer = writer

        # cache
        if False:
            self.__cachedir = '.raftcache'
            if not os.path.exists(self.__cachedir):
                os.mkdir(self.__cachedir)
            self.__cache = QtNetwork.QNetworkDiskCache()
            self.__cache.setCacheDirectory(self.__cachedir)
            self.setCache(self.__cache)
        else:
            self.__cache = NetworkCacheL(self)
            self.__cache = NetworkMemoryCache(self)
            self.setCache(self.__cache)

        # persistent storage
        self.__storagedir = '.raftstorage'
        if not os.path.exists(self.__storagedir):
            os.mkdir(self.__storagedir)
        settings = QtWebKit.QWebSettings.globalSettings()
        settings.setAttribute(QtWebKit.QWebSettings.AutoLoadImages, False)
        settings.setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)
        settings.setAttribute(QtWebKit.QWebSettings.LocalStorageEnabled, True)
#        settings.setAttribute(QtWebKit.QWebSettings.JavascriptEnabled, False)
        settings.enablePersistentStorage(self.__storagedir)
        settings.setLocalStoragePath(self.__storagedir)
        
        # cookie jar
        self.__cookiejar = CookieJar()
        self.setCookieJar(self.__cookiejar)

        # no proxy
#        proxy = QtNetwork.QNetworkProxy(QtNetwork.QNetworkProxy.HttpProxy, 'localhost', 8080)
#        self.setProxy(proxy)

        QObject.connect(self, SIGNAL('finished(QNetworkReply *)'), self.replyFinished)

    def createRequest(self, operation, request, outgoingData = None):
        if outgoingData:
            outgoingData = WrapIODevice(outgoingData)
        reply =  NetworkReply(self, self.writer, request, outgoingData, QtNetwork.QNetworkAccessManager.createRequest(self, operation, request, outgoingData))
        return reply

    def replyFinished(self, reply):
        # check for redirect
        redirectTarget = reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute)
        if redirectTarget:
            targetUrl = redirectTarget
            if not targetUrl.isEmpty():
                if targetUrl.isRelative():
                    targetUrl = reply.url().resolved(targetUrl)
                # simple redirect policy
                if targetUrl != reply.url():
                    originatingObject = reply.request().originatingObject()
                    if originatingObject and (reply.url() == originatingObject.requestedUrl()):
                        originatingObject.setUrl(targetUrl)

class setTimeoutWrapper(QObject):
    def __init__(self, parent):
        QObject.__init__(self, parent)

    @PyQt4.QtCore.pyqtProperty(int)
    def blah(self):
        return 1234

    def __call__(self):
        return self

    def foo(self):
        return('bar')

class WebPage(QtWebKit.QWebPage):
    def __init__(self, parent, browserWindow, mainWindow, spider):
        QtWebKit.QWebPage.__init__(self, parent)
        self.__browserWindow = browserWindow
        self.__mainWindow = mainWindow
        self.__spider = spider
        QObject.connect(self, SIGNAL('frameCreated(QWebFrame*)'), self.frameCreatedHandler)

    @PyQt4.QtCore.pyqtSlot(name='shouldInterruptJavaScript', result='bool')
    def shouldInterruptJavaScript(self):
        print('*** shouldInterruptJavaScript')
        return True

    def javaScriptAlert(self, frame, msg):
        print(('alert from [%s / %s]: %s' % (frame.url(), frame.requestedUrl(), msg)))

    def javaScriptConfirm(self, frame, msg):
        print(('confirm from [%s / %s]: %s' % (frame.url(), frame.requestedUrl(), msg)))

    def javaScriptPrompt(self, frame, msg, defaultValue, result):
        print(('prompt from [%s / %s]: %s' % (frame.url(), frame.requestedUrl(), msg)))

    def javaScriptConsoleMessage(self, message, lineNumber, sourceID):
        print(('console log from [%s / %s]: %s' % (lineNumber, sourceID, message)))

    def userAgentForUrl(self, url):
        return 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.21.1 (KHTML, like Gecko) Version/5.0.5 Safari/533.21.1'
    
    def acceptNavigationRequest(self, frame, request, navType):
        fUrl = ''
        pfUrl = ''
        if frame:
            fUrl = frame.url().toString(QUrl.FullyEncoded)
        pf = frame.parentFrame()
        if pf is not None:
            pfUrl = pf.url().toString(QUrl.FullyEncoded)
        print(('navigation request to --> %s from %s | %s' % (request.url().toString(QUrl.FullyEncoded), fUrl, pfUrl)))
        if self.__browserWindow.processing_links:
            if request.url().isValid() and frame.url().host() == request.url().host() and frame.url() != request.url():
                self.__mainWindow.emit(SIGNAL('addTargetUrl(QUrl,QWebFrame)'), request.url(), frame)
#            self.__mainWindow.addTargetUrlHandler(QUrl('about:blank'))
            return False
        else:
            return True

    def frameCreatedHandler(self, frame):
        print(('--> new frame created: %s' % (frame)))
        QObject.connect(frame, SIGNAL('javaScriptWindowObjectCleared()'), self.javaScriptWindowObjectClearedHandler)

    def javaScriptWindowObjectClearedHandler(self):
        print('---->javaScriptWindowObjectCleared (page level)')

class BrowserWindow(QWidget):
    def __init__(self, parent, mainWindow, index, exclude_patterns, spider, images):
        QWidget.__init__(self, parent)
        self.__mainWindow = mainWindow
        self.__index = index
        self.__spider = spider
        self.__exclude_patterns = exclude_patterns
#        self.__images = images
        self.__url = None
        self.__loaded = False
        self.logger = self.__mainWindow.logger
        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(0,0,600,10)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.webview = QtWebKit.QWebView(self)
        self.webview.setGeometry(10, 45, 600, 480)
        self.webview.setPage(WebPage(self.webview, self, mainWindow, spider))
        self.webview.page().setNetworkAccessManager(self.__mainWindow.networkManager)
        self.processing_links = False
        if images:
            self.webview.settings().setAttribute(QtWebKit.QWebSettings.AutoLoadImages, True)
            
        self.qtimer = QTimer()
        self.qlock = QMutex()
        QObject.connect(self.webview, SIGNAL('loadFinished(bool)'), self.loadFinishedHandler)
        QObject.connect(self.webview, SIGNAL('loadProgress(int)'), self.loadProgressHandler)
        QObject.connect(self, SIGNAL('navigate(QString)'), self.navigateHandler)
        QObject.connect(self.qtimer, SIGNAL('timeout()'), self.timeoutHandler)
        QObject.connect(self.webview.page().mainFrame(), SIGNAL('javaScriptWindowObjectCleared()'), self.javaScriptWindowObjectClearedHandler)
        self.webview.page().mainFrame().addToJavaScriptWindowObject('setInterval', setTimeoutWrapper(self))

    def javaScriptWindowObjectClearedHandler(self):
        print('---->javaScriptWindowObjectCleared')
        self.webview.page().mainFrame().addToJavaScriptWindowObject('setInterval', setTimeoutWrapper(self))

    def navigateHandler(self, url):
        self.__url = url
        self.__loaded = False
        if self.qtimer.isActive():
            self.qtimer.stop()
        self.qtimer.start(30000) # seconds to finish
        self.logger.info('loading: %s' % url)
        self.webview.load(QUrl(url))

    def loadFinishedHandler(self, ok):
        if self.__loaded:
            return
        if self.webview.url() != self.webview.page().mainFrame().requestedUrl():
            # redirecting ...
            pass
        else:
            self.logger.info('load finished %s: %s' % (self.webview.url().toString(), ok))
            self.__loaded = True
            if self.qtimer.isActive():
                self.qtimer.stop()
            if ok:
                # give page 1 seconds for page to settle
                self.qtimer.start(1000)
            else:
                self.callNavigationFinished()

    def loadProgressHandler(self, progress):
        self.progressBar.setValue(progress)

    def timeoutHandler(self):
        self.logger.debug('timeoutHandler() called for %s' % (self.__url))
        if self.qtimer.isActive():
            self.qtimer.stop()
        if not self.__loaded:
            self.logger.warn('forcibly stopping page: %s' % (self.__url))
            self.webview.stop()
        self.callNavigationFinished()

    def shouldAddTarget(self, frame, baseUrl, resolvedUrl):
        path1 = frame.url().path()
        path2 = baseUrl.path()
        path3 = resolvedUrl.path()
        if path1 != path3 and path2 != path3 and resolvedUrl.host() == frame.url().host():
            return True
        return False

    def processFrame(self, frame):
        print(('processing frame [%s]: %s' % (frame.frameName(), frame.url().toString(QUrl.FullyEncoded))))
        baseUrl = frame.url()
        dom = frame.documentElement()
        headElement = dom.findFirst('head')
        if headElement:
            baseElement = headElement.findFirst('base')
            if baseElement:
                baseHref = baseElement.attribute('href')
                # TODO: handle target
                if baseHref and 0 != baseHref.length():
                    baseUrl = QUrl(baseHref)

        if self.__spider:
            # forms
            forms = dom.findAll("form")
            for form in forms:
                inputs = form.findAll("input")
                submits = []
                for inp in inputs:
                    typ = inp.attribute('type')
                    print(typ)
                    if str(typ).lower() == 'submit':
                        submits.append(inp)
                        
                for submit in submits:
                    pass

                for aname in form.attributeNames():
                    print(('%s: %s' % (aname, form.attribute(aname))))
            # links
            alinks = dom.findAll("a")
            for alink in alinks:
                for aname in alink.attributeNames():
                    if 'href' != str(aname).lower():
                        continue
                    href = alink.attribute(aname)
                    hrefUrl = QUrl(href)
                    if hrefUrl.isValid():
                        print(('href=%s' % href))
                        if hrefUrl.scheme() == 'javascript':
                            print(('evaluating javascript->%s' % hrefUrl.path()))
                            alink.evaluateJavaScript(hrefUrl.path())
                        else:
                            if hrefUrl.isRelative():
                                resolvedUrl = baseUrl.resolved(hrefUrl)
                            else:
                                resolvedUrl = hrefUrl
                            if self.shouldAddTarget(frame, baseUrl, resolvedUrl):
                                self.__mainWindow.emit(SIGNAL('addTargetUrl(QUrl)'), resolvedUrl)
                    else:
                        print(('ignoring invalid href=%s' % href))
#                    print('%s: %s' % (aname, alink.attribute(aname)))
#        print(buffer(dom.toOuterXml()))

        html = dom.toOuterXml()

#        print(html)
        for child in frame.childFrames():
            self.processFrame(child)

    def callNavigationFinished(self):
        mainFrame = self.webview.page().mainFrame()
        self.processing_links = True
        self.processFrame(mainFrame)
        securityOrigin = mainFrame.securityOrigin()
        databases = securityOrigin.databases()
        for database in databases:
            print(('database=%s' % (database.fileName())))
        self.processing_links = False
        self.__mainWindow.emit(SIGNAL('navigationFinished(int, QString)'), self.__index, self.__url)
            
class WriterThread(QThread):
    def __init__(self, directory, logger):
        QThread.__init__(self)
        now = time.time()
        self.logger = logger
        self.filename = os.path.join(directory, 'RaftCapture-%d.xml.xz' % (int(now*1000)))
        self.re_nonprintable = re.compile(bytes('[^%s]' % re.escape('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r'), 'ascii'))
        self.ofhandle = lzma.LZMAFile(self.filename, 'wb')
        self.ofhandle.write(b'<raft version="1.0">')
        self.qlock = QMutex()
        self.datalist = collections.deque()
        self.timer = QTimer()
        QObject.connect(self.timer, SIGNAL('timeout()'), self.processData)
        self.timer.start(100)

    def run(self):
        QObject.connect(self, SIGNAL('quit()'), self.quitHandler, Qt.QueuedConnection)
        self.exec_()

    def write(self, data):
        self.qlock.lock()
        try:
            self.datalist.append(data)
        finally:
            self.qlock.unlock()

    def processData(self):
        if self.qlock.tryLock(1000):
            try:
                if len(self.datalist)>0:
                    data = self.datalist.popleft()
#                    self.logger.debug('--->processData: %s' % data[1])
                    self.writeData(data)
            finally:
                self.qlock.unlock()

    def writeData(self, data):
        """
        [0] - method
        [1] - url
        [2] - host
        [3] - datetime
        [4] - request headers
        [5] - request body
        [6] - status
        [7] - elapsed
        [8] - content type
        [9] - content length
        [10] - response headers
        [11] - response body
        """
        ohandle = io.StringIO()
        ohandle.write('<capture>\n')
        ohandle.write('<request>\n')
        ohandle.write('<method>%s</method>\n' % escape(data[0]))
        ohandle.write('<url>%s</url>\n' % escape(data[1]))
        ohandle.write('<host>%s</host>\n' % escape(data[2]))
        # TODO: FIXMES
        # ohandle.write('<hostip>%s</hostip>\n' % ???)
        ohandle.write('<datetime>%s</datetime>\n' % escape(time.asctime(time.gmtime(data[3]))+' GMT'))
        request_headers = data[4]
        request_body = data[5]
        if self.re_nonprintable.search(request_headers):
            ohandle.write('<headers encoding="base64">%s</headers>\n' % base64.b64encode(request_headers).decode('ascii'))
        else:
            ohandle.write('<headers>%s</headers>\n' % escape(request_headers.decode('ascii')))
        if request_body:
            if self.re_nonprintable.search(request_body):
                ohandle.write('<body encoding="base64">%s</body>\n' % base64.b64encode(request_body).decode('ascii'))
            else:
                ohandle.write('<body>%s</body>\n' % escape(request_body.decode('ascii')))
        ohandle.write('</request>\n')
        ohandle.write('<response>\n')
        ohandle.write('<status>%d</status>\n' % int(data[6]))
        ohandle.write('<elapsed>%d</elapsed>\n' % int(data[7]))
        ohandle.write('<content_type>%s</content_type>\n' % escape(data[8]))
        ohandle.write('<content_length>%d</content_length>\n' % int(data[9]))
        response_headers = data[10]
        response_body = data[11]
        if self.re_nonprintable.search(response_headers):
            ohandle.write('<headers encoding="base64">%s</headers>\n' % base64.b64encode(response_headers).decode('ascii'))
        else:
            ohandle.write('<headers>%s</headers>\n' % escape(response_headers.decode('ascii')))
        if response_body:
            if self.re_nonprintable.search(response_body):
                ohandle.write('<body encoding="base64">%s</body>\n' % base64.b64encode(response_body).decode('ascii'))
            else:
                ohandle.write('<body>%s</body>\n' % escape(response_body.decode('ascii')))
        ohandle.write('</response>\n')
        ohandle.write('</capture>\n')

        self.ofhandle.write(ohandle.getvalue().encode('utf-8')) # TODO: should use utf-8 universally?

    def finishWrite(self):
        self.qlock.lock()
        while len(self.datalist)>0:
            self.writeData(self.datalist.popleft())
        self.ofhandle.write(b'</raft>')
        self.ofhandle.close()

    def shutdown(self):
        self.finishWrite()
        self.exit(0)

    def quitHandler(self):
        logger.info('got quit()')
        self.exit(0)

class MainWindow(QWidget):
    def __init__(self, targets, skips = [], spider = False, images = False, parent = None):

        QWidget.__init__(self, parent)
        self.qlock = QMutex()

        self.logger = logging.getLogger(__name__)
        self.logger.info('starting...')

        self.resize(800, 600)
        self.setWindowTitle('RAFT Crawler')

        self.num_tabs = 4
        
        self.qtab = QTabWidget(self)
        self.qtab.setGeometry(10, 45, 650, 530)

        self.qbutton = QPushButton('Close', self)
        self.qbutton.setGeometry(10, 10, 60, 35)
        self.connect(self.qbutton, SIGNAL('clicked()'), self.quit)

        self.gbutton = QPushButton('Go', self)
        self.gbutton.setGeometry(70, 10, 60, 35)
        self.connect(self.gbutton, SIGNAL('clicked()'), self.go)

        self.qlineedit = QLineEdit(self)
        self.qlineedit.setGeometry(130, 10, 400, 35)

        QObject.connect(self, SIGNAL('navigationFinished(int, QString)'), self.navigationFinishedHandler)
        QObject.connect(self, SIGNAL('addTargetUrl(QUrl)'), self.addTargetUrlHandler)
        QObject.connect(self, SIGNAL('waitForOutstanding()'), self.waitForOutstandingHandler)
        qApp.setQuitOnLastWindowClosed(False)
        qApp.lastWindowClosed.connect(self.quit)

        self.writer = WriterThread('.', logger)
        self.writer.start()

        self.networkManager = NetworkManager(self.writer)

        self.exclude_patterns = []
        for skip in skips:
            self.exclude_patterns.append(re.compile(skip, re.I))

        self.browsers = []
        self.available = []
        for i in range(0, self.num_tabs):
            tab = QWidget()
            self.qtab.addTab(tab, 'Tab %d' % i)
            self.browsers.append(BrowserWindow(tab, self, i, self.exclude_patterns, spider, images))
            self.available.append(True)

        self.index = 0
        self.targets = targets
        self.targets_outstanding = {}
        self.link_count = {}

        self.connect(self, SIGNAL('quit()'), self.quit)
        self.automode = False
        if len(self.targets) > 0:
            self.automode = True
            self.go()
        
    def quit(self):
        if self.writer.isRunning():
            self.writer.shutdown()
            self.logger.debug('waiting for thread... finished = %s', self.writer.isFinished())
            self.writer.wait(500)
        self.logger.debug('exiting... finished = %s', self.writer.isFinished())
        self.logger.info('quitting...')
        QTimer.singleShot(0, qApp, SLOT('quit()'))

    def go(self):
        self.qlock.lock()
        try:
            entry = self.qlineedit.text()
            if entry:
                entry = QUrl.fromUserInput(entry).toEncoded().data().decode('utf-8')
                self.targets.append(entry)
                self.qlineedit.setText('')
            for target in self.targets:
                self.targets_outstanding[target] = True
        finally:
            self.qlock.unlock()

        self.dispatchNext()

    def waitForOutstandingHandler(self):
        self.qlock.lock()
        outstanding = len(self.targets_outstanding)
        if outstanding > 0:
            self.logger.debug('waiting for [%d] outstanding' % (outstanding))
            self.qlock.unlock()
            self.dispatchNext()
        else:
            self.qlock.unlock()
            QTimer.singleShot(1000, self, SIGNAL('quit()'))

    def addTargetUrlHandler(self, url):
        if not self.qlock.tryLock(1000):
            self.logger.debug('failed to lock for url %s\n' % (url))
            return
        else:
            self.logger.debug('locked after tryLock')

        try:
            target = url.toString(QUrl.FullyEncoded)
            for pat in self.exclude_patterns:
                if pat.search(target):
                    self.logger.warn('excluding target: %s\n' % (target))
                    return
            if not target in self.targets:
                host = url.host()
                if host in self.link_count:
                    if self.link_count[host] > MAX_LINK_COUNT:
                        return
                    else:
                        self.link_count[host] += 1
                else:
                    self.link_count[host] = 1
                print(('adding target [%s]' % (target)))
                self.targets_outstanding[target] = True
                self.targets.append(target)
        finally:
            self.qlock.unlock()
                
    def navigationFinishedHandler(self, index, url):
        if not self.qlock.tryLock(1000):
            self.logger.debug('failed to lock for url %s and index %d\n' % (url, index))
            return
        else:
            self.logger.debug('locked after tryLock')
        try:
            target = url
            if target not in self.targets_outstanding:
                self.logger.debug('unexpected target: %s, %s' % (target, repr(self.targets_outstanding)))
            else:
                self.logger.debug('removing outstanding: %s' % (target))
                self.targets_outstanding.pop(target)

            self.available[index] = True
            self.qlock.unlock()
        except:
            self.qlock.unlock()

        self.dispatchNext()

    def dispatchNext(self):
        self.qlock.lock()
        try:
            for i in range(0, self.num_tabs):
                if self.index < len(self.targets):
                    if self.available[i]:
                        target = self.targets[self.index]
                        self.logger.debug('dispatching target: %s to %d' % (target, i))
                        self.available[i] = False
                        self.browsers[i].emit(SIGNAL('navigate(QString)'), target)
                        self.index += 1
                elif self.automode:
                    self.qlock.unlock()
                    self.logger.debug('all targets dispatched ... waiting')
                    QTimer.singleShot(1000, self, SIGNAL('waitForOutstanding()'))
                    break
            else:
                self.qlock.unlock()
        except:
            self.qlock.unlock()
            raise

def capture_error(typ, val, traceb):
    import traceback
    print(('type=%s, value=%s\n%s' % (typ, val, traceback.format_tb(traceb))))

if '__main__' == __name__:

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    targets = []
    skips = []
    spider = False
    images = False
    if len(sys.argv) > 1:
        # file
        fileargs = []
        i = 1
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg.startswith('-'):
                if arg[1:] in ('spider',):
                    spider = True
                elif arg[1:] in ('images',):
                    images = True
                elif arg[1:] in ('X','exclude'):
                    skips.extend([x.strip() for x in sys.argv[i+1].split(',')])
                    i += 1
            else:
                fileargs.append(arg)
            i += 1
        
        for arg in fileargs:
            if os.path.exists(arg):
                for line in open(arg, 'r'):
                    target = line.rstrip()
                    if not (target.startswith('http:') or target.startswith('https:')):
                        target = QUrl.fromUserInput(target).toEncoded().data().decode('utf-8')
                    targets.append(target)
            else:
                target = arg
                if not (target.startswith('http:') or target.startswith('https:')):
                    target = QUrl.fromUserInput(target).toEncoded().data().decode('utf-8')
                targets.append(target)

    app = QApplication([])
    main = MainWindow(targets, skips, spider, images)
    main.show()

    sys.excepthook = capture_error

    sys.exit(app.exec_())


