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
from PyQt4.QtNetwork import QNetworkCookie
from urllib2 import urlparse
import re

from core.data.SiteMapModel import SiteMapNode
from core.database.constants import ResponsesTable

class SiteMapThread(QThread):
    def __init__(self, framework, treeViewModel, parent = None):
        QThread.__init__(self, parent)
        self.framework = framework
        self.treeViewModel = treeViewModel
        self.qtimer = QTimer()
        self.qlock = QMutex()
        self.fillAll = False
        QObject.connect(self, SIGNAL('quit()'), self.quitHandler)
        QObject.connect(self, SIGNAL('started()'), self.startedHandler)

        self.re_set_cookie = re.compile(r'^Set-Cookie2?:\s*(.+)$', re.I|re.M)

        self.lastId = 0
        self.Data = None
        self.cursor = None

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.populateSiteMap(True)

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None

    def run(self):
        QObject.connect(self, SIGNAL('updateSiteMap()'), self.doUpdateSiteMap, Qt.DirectConnection)
        self.framework.subscribe_response_data_added(self.doUpdateSiteMap)
        self.exec_()

    def quitHandler(self):
        self.framework.debug_log('SiteMapThread quit...')
        self.close_cursor()
        self.exit(0)

    def startedHandler(self):
        self.framework.debug_log('SiteMapThread started...')
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)
        
    def populateSiteMap(self, fillAll):
        self.fillAll = fillAll
        QTimer.singleShot(50, self, SIGNAL('updateSiteMap()'))

    def doUpdateSiteMap(self):
        if not self.qlock.tryLock():
            return
        try:

            if self.fillAll:
                self.fillAll = False
                self.treeViewModel.clearModel()
                self.lastId = 0

            rows = self.Data.get_sitemap_info(self.cursor, self.lastId)

            global_cookie_jar = self.framework.get_global_cookie_jar()

            count = 0
            for row in rows:
                count += 1
                if 0 == (count % 100):
                    self.yieldCurrentThread()

                rowItems = [m or '' for m in list(row)]

                Id = str(rowItems[0])
                try:
                    self.lastId = int(Id)
                except ValueError:
                    pass

                url = str(rowItems[1])
                status = str(rowItems[2])
                response_headers = str(rowItems[3])
                # TODO: make configurable
                if status in ('400', '404', '500', '501'):
                    continue

                # TODO: 
                m = self.re_set_cookie.search(response_headers)
                if m:
                    setCookies = m.group(1)
                    cookieList = QNetworkCookie.parseCookies(setCookies)
                    global_cookie_jar.setCookiesFromUrl(cookieList, QUrl.fromEncoded(url))

                parsed = urlparse.urlsplit(url)
                hostname = parsed.hostname.lower()
                hostloc = urlparse.urlunsplit((parsed.scheme, parsed.netloc, '/','',''))

                rootNode = self.treeViewModel.findOrAddNode(hostname)
                hostLocNode = rootNode.findOrAddNode(self.treeViewModel, hostloc)
                pathval = parsed.path

                # add directories
                parentNode = hostLocNode
                parentNode.setResponseId(None, hostloc)
                lastSlash = 0
                slash = 0
                while True:
                    slash = pathval.find('/', slash+1)
                    if slash < 0:
                        break
                    dirname = pathval[lastSlash+1:slash+1]
                    parentNode = parentNode.findOrAddNode(self.treeViewModel, dirname)
                    parentNode.setResponseId(None, urlparse.urlunsplit((parsed.scheme, parsed.netloc, pathval[0:slash+1],'','')))
                    lastSlash = slash

                # add file element
                if lastSlash+1 < len(pathval):
                    filename = pathval[lastSlash+1:]
                    parentNode = parentNode.findOrAddNode(self.treeViewModel, filename)
                    parentNode.setResponseId(None, urlparse.urlunsplit((parsed.scheme, parsed.netloc, pathval,'','')))

                # add query
                if parsed.query:
                    parentNode = parentNode.findOrAddNode(self.treeViewModel, '?'+parsed.query)

                # store the latest Id
                # TODO: should determine best candidate to display
                parentNode.setResponseId(Id, url)

        finally:
            self.qlock.unlock()
