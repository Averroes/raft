#
# Implements a web page for web spidering
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

import PyQt4
from PyQt4 import QtWebKit, QtNetwork
from PyQt4.QtCore import *

from core.web.BaseWebPage import BaseWebPage

class SpiderWebPage(BaseWebPage):
    def __init__(self, framework, pageController, parent = None):
        BaseWebPage.__init__(self, framework, parent)
        self.framework = framework
        self.pageController = pageController
        self.loadFinished.connect(self.handle_loadFinished)
        self.frameCreated.connect(self.handle_frameCreated)
        self.configure_frame(self.mainFrame())

    def set_page_settings(self, settings):
        # common settings handled by base
        settings.setAttribute(QtWebKit.QWebSettings.JavascriptCanOpenWindows, True)

    def handle_frameCreated(self, frame):
        self.configure_frame(frame)

    def configure_frame(self, frame):
        self.add_javascript_window_object(frame)
        QObject.connect(frame, SIGNAL('loadFinished(bool)'), lambda x: self.handle_frame_loadFinished(frame, x))
        QObject.connect(frame, SIGNAL('javaScriptWindowObjectCleared()'), lambda: self.handle_javaScriptWindowObjectCleared(frame))

    def handle_loadFinished(self, ok):
        self.add_javascript_window_object(self.mainFrame())

    def handle_frame_loadFinished(self, frame, ok):
        print('frame load finished', ok)
        self.add_javascript_window_object(frame)

    def process_page_events(self, frame):
        print('process page events called.....')
        if self.pageController.phase_extract_links():
            self.extract_links(frame)
        elif self.pageController.phase_mouse_events():
            self.generate_mouse_events(frame)
        elif self.pageController.phase_text_events():
            self.generate_text_events(frame)
        elif self.pageController.phase_javascript_events():
            self.generate_javascript_events(frame)

    def handle_javaScriptWindowObjectCleared(self, frame):
        self.add_javascript_window_object(frame)

    def add_javascript_window_object(self, frame):
        frame.addToJavaScriptWindowObject("__RAFT__", self)
        frame.evaluateJavaScript("""
__RAFTSCRIPT__ = {
'send_mouse_motion_events' : function(obj) {
try {
  var evt = document.createEvent("MouseEvent");
  evt.initMouseEvent("mouseover", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
  obj.dispatchEvent(evt);
  var evt = document.createEvent("MouseEvent");
  evt.initMouseEvent("mouseout", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
  obj.dispatchEvent(evt);
  var evt = document.createEvent("MouseEvent");
  evt.initMouseEvent("mousemove", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
  return obj.dispatchEvent(evt);
} catch(e) {
 window.__RAFT__.report_error(''+e);
}
},
'send_mouse_click_events' : function(obj) {
try {
  var evt = document.createEvent("MouseEvent");
  evt.initMouseEvent("mousedown", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
  obj.dispatchEvent(evt);

  var evt = document.createEvent("MouseEvent");
  evt.initMouseEvent("mouseup", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
  obj.dispatchEvent(evt);

  var evt = document.createEvent("MouseEvent");
  evt.initMouseEvent("click", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
  obj.dispatchEvent(evt);

  var evt = document.createEvent("MouseEvent");
  evt.initMouseEvent("dblclick", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
  return obj.dispatchEvent(evt);
} catch(e) {
 window.__RAFT__.report_error(''+e);
}
},
'init_key_event' : function(name, charCode) {
  var evt = document.createEvent('KeyboardEvent');
  evt.initKeyboardEvent(name, true, true, window, false, false, false, false, charCode, charCode);
  if (evt.charCode == 0) {
    evt = document.createEvent('Event');
    evt.initEvent(name, true, true);
    evt.view = window;
    evt.altKey = false;
    evt.ctrlKey = false;
    evt.shiftKey = false;
    evt.metaKey = false;
    evt.charCode = charCode;
    evt.keyCode = charCode;
    evt.which = charCode;
  }
  return evt;
},
'send_text_key_events' : function(obj) {
try {
  var charCode = "T".charCodeAt(0);
  var evt = this.init_key_event("keydown", charCode);
  obj.dispatchEvent(evt);

  var evt = this.init_key_event("keypress", charCode);
  obj.dispatchEvent(evt);

  var evt = this.init_key_event("keyup", charCode);
  obj.dispatchEvent(evt);

  var evt = document.createEvent('TextEvent');
  evt.initTextEvent("textInsert", true, true, window, "test");
  obj.dispatchEvent(evt)

} catch(e) {
 window.__RAFT__.report_error(''+e);
}
},
'send_text_enter_events' : function(obj) {
try {
  charCode = 13;
  var evt = this.init_key_event("keydown", charCode);
  obj.dispatchEvent(evt);

  var evt = this.init_key_event("keypress", charCode);
  obj.dispatchEvent(evt);

  var evt = this.init_key_event("keyup", charCode);
  obj.dispatchEvent(evt);

} catch(e) {
 window.__RAFT__.report_error(''+e);
}
},
};
console.log(__RAFTSCRIPT__);
""")

    @PyQt4.QtCore.pyqtSlot(name='shouldInterruptJavaScript', result='bool')
    def shouldInterruptJavaScript(self):
        self.pageController.log('console', self.url(), '*** shouldInterruptJavaScript invoked')
        return True

    @PyQt4.QtCore.pyqtSlot(QVariant, name='report_error')
    def report_error(self, message):
        print('GOT ERROR: %s' % (str(message.toString())))
        
    def javaScriptAlert(self, frame, msg):
        self.pageController.log('alert', frame.url(), msg)

    def javaScriptConfirm(self, frame, msg):
        self.pageController.log('confirm', frame.url(), msg)
        return False

    def javaScriptPrompt(self, frame, msg, defaultValue, result):
        self.pageController.log('prompt', frame.url(),  msg)
        return False

    def javaScriptConsoleMessage(self, message, lineNumber, sourceID):
        print('CONSOLE--->', str(message))
        self.pageController.log('console', self.mainFrame().url(), 'log from [%s / %s]: %s' % (lineNumber, sourceID, message))

    def userAgentForUrl(self, url):
        return self.framework.useragent()

    def acceptNavigationRequest(self, frame, request, navigationType):
        return self.pageController.acceptNavigation(frame, request, navigationType)

    def extract_links(self, frame):
        dom = frame.documentElement()
        processed = []
        for webElement in dom.findAll('*'):
            if webElement in processed:
                break
            processed.append(webElement)
###->            print('tagname => %s' % str(webElement.tagName()))
            for aname in webElement.attributeNames():
                lname = str(aname).lower()
                if lname in ('href', 'src'):
                    avalue = webElement.attribute(aname)
                    hrefUrl = QUrl(avalue)
                    if hrefUrl.isValid() and hrefUrl.scheme() == 'javascript':
                        webElement.evaluateJavaScript(hrefUrl.path())

    def generate_mouse_events(self, frame):
        dom = frame.documentElement()
        processed = []
        for webElement in dom.findAll('*'):
            if webElement in processed:
                break
            processed.append(webElement)
###->            print('(mouse) tagname => %s' % str(webElement.tagName()))
            webElement.evaluateJavaScript('window.__RAFTSCRIPT__.send_mouse_motion_events(this)')
        for webElement in processed:
            webElement.evaluateJavaScript('window.__RAFTSCRIPT__.send_mouse_click_events(this)')

    def generate_text_events(self, frame):
        dom = frame.documentElement()
        processed = []
        for webElement in dom.findAll('*'):
            if webElement in processed:
                break
            processed.append(webElement)
            webElement.evaluateJavaScript('window.__RAFTSCRIPT__.send_text_key_events(this);')
        for webElement in processed:
            webElement.evaluateJavaScript('window.__RAFTSCRIPT__.send_text_enter_events(this);')

    def generate_javascript_events(self, frame):
        dom = frame.documentElement()
        processed = []
        formElements = []
        for webElement in dom.findAll('*'):
            if webElement in processed:
                break
            processed.append(webElement)
            tagName = str(webElement.tagName())
            if 'FORM' == tagName.upper():
                formElements.append(webElement)
                continue
###->            print('(js) tagname => %s' % tagName)
            for aname in webElement.attributeNames():
                attr_name = str(aname)
                lname = attr_name.lower()
                if lname.startswith('on'):
###->                    print('             %s' % (attr_name[2:]))
                    webElement.evaluateJavaScript('this.%s();' % attr_name[2:])
        for webElement in formElements:
            for aname in webElement.attributeNames():
                lname = str(aname).lower()
                if lname == 'onsubmit':
                    avalue = webElement.attribute(aname)
                    webElement.evaluateJavaScript(avalue)
                elif lname.startswith('on'):
                    avalue = webElement.attribute(aname)
                    webElement.evaluateJavaScript(avalue)

        # finally, try to submit forms in reverse order
        # TODO: this may navigate the page to new page
        self.pageController.set_extraction_finished(True)
        formElements.reverse()
        for webElement in formElements:
            webElement.evaluateJavaScript('this.target="_blank";')
            webElement.evaluateJavaScript('this.onsubmit=function(){return true;}')
            webElement.evaluateJavaScript('this.submit()')
            submitElements = webElement.findAll('input[type=submit]')
            processed = []
            for element in submitElements:
                if element in processed:
                    break
                element.evaluateJavaScript('this.click();')
                    
