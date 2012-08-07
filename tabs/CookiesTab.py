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
from PyQt4.QtCore import Qt, QObject, SIGNAL, QDateTime
from PyQt4.QtGui import *
from PyQt4.QtNetwork import QNetworkCookie

from core.data.LocalStorage import LocalStorage
from core.data.FlashCookies import FlashCookies

from cStringIO import StringIO
import bz2
import time
from lxml import etree

class CookiesTab(QObject):
    def __init__(self, framework, mainWindow):
        QObject.__init__(self, mainWindow)
        self.framework = framework
        self.mainWindow = mainWindow

        self.mainWindow.cookiesTabWidget.currentChanged.connect(self.handle_cookiesTab_currentChanged)
        self.mainWindow.cookiesCookieJarTreeWidget.itemClicked.connect(self.handle_cookiesTreeWidget_itemClicked)
        self.mainWindow.cookiesCookieJarSaveButton.clicked.connect(self.handle_cookiesSave_clicked)
        self.mainWindow.cookiesCookieJarDeleteButton.clicked.connect(self.handle_cookiesDelete_clicked)
        self.mainWindow.cookiesCookieExportCookieJarButton.clicked.connect(self.handle_cookiesExportCookieJar_clicked)
        self.mainWindow.cookiesCookieImportCookieJarButton.clicked.connect(self.handle_cookiesImportCookieJar_clicked)

        self.mainWindow.cookiesLocalStorageTreeWidget.itemClicked.connect(self.handle_localStorageTreeWidget_itemClicked)
        self.mainWindow.cookiesLocalStorageSaveButton.clicked.connect(self.handle_localStorageSave_clicked)
        self.mainWindow.cookiesLocalStorageDeleteButton.clicked.connect(self.handle_localStorageDelete_clicked)

        self.localStorage = LocalStorage(self.framework)
        self.flashCookies = FlashCookies(self.framework)
        
        self.Data = None
        self.cursor = None
        self.framework.subscribe_database_events(self.db_attach, self.db_detach)
        self.framework.subscribe_cookie_jar_updated(self.populate_cookie_jar_tree)

    def db_attach(self):
        self.Data = self.framework.getDB()
        self.cursor = self.Data.allocate_thread_cursor()
        self.fill_cookies_tab()

    def db_detach(self):
        self.close_cursor()
        self.Data = None

    def close_cursor(self):
        if self.cursor and self.Data:
            self.cursor.close()
            self.Data.release_thread_cursor(self.cursor)
            self.cursor = None


    def fill_cookies_tab(self):
        index = self.mainWindow.cookiesTabWidget.currentIndex()
        if 0 == index:
            self.populate_cookie_jar_tree()
        elif 1 == index:
            # flash
            self.populate_flash_cookies_tree()
        elif 2 == index:
            self.populate_local_storage_tree()
        else:
            pass

    def handle_cookiesTab_currentChanged(self):
        self.fill_cookies_tab()

    def handle_cookiesTreeWidget_itemClicked(self, item, column):
        domain = str(item.text(0))
        name = str(item.text(1))
        if domain and name:
            cookieList = self.framework.get_global_cookie_jar().allCookies()
            cookie = self.find_cookie_by_domain_and_name(cookieList, domain, name)
            if cookie:
                self.populate_cookieJar_edit_fields(cookie)
        else:
            self.clear_cookieJar_edit_fields(domain)

    def handle_cookiesExportCookieJar_clicked(self):
        # TODO: refactor and move to raftparse routines
        cookieJar = self.framework.get_global_cookie_jar()
        cookieList = cookieJar.allCookies()
        results = StringIO()
        results.write('<cookies>\n')
        for cookie in cookieList:
            results.write('<cookie>\n')
            results.write('<raw encoding="base64">%s</raw>\n' % str(cookie.toRawForm().data()).encode('base64'))
            results.write('</cookie>\n')
        results.write('</cookies>\n')
        filename = 'CookieExport-%s' % int(time.time())
        file = QFileDialog.getSaveFileName(None, "Export Cookie Jar to file", filename, "XML File (*.xml);;BZ2 XML File (*.xml.bz2)")
        if file and str(file):
            filename = str(file)
            if filename.endswith('.xml.bz2'):
                filename = filename.replace('.xml.bz2.xml.bz2', '.xml.bz2')
                fh = bz2.BZ2File(filename, 'w')
            elif filename.endswith('.xml'):
                filename = filename.replace('.xml.xml', '.xml')
                fh = open(filename, 'wb')
            else:
                raise Exception('unhandled file type: %s' % (filename))
            fh.write(results.getvalue())
            fh.close()
            
    def load_cookies_from_file(self, filename):
        cookieList = []

        if filename.endswith('.xml.bz2'):
            source = bz2.BZ2File(filename, 'r')
        elif filename.endswith('.xml'):
            source = open(filename, 'r')
        else:
            raise Exception('unhandled file type: %s' % (filename))

        # http://effbot.org/zone/element-iterparse.htm#incremental-parsing
        context = etree.iterparse(source, events=('start', 'end'), huge_tree = True)
        iterator = iter(context)
        root = None

        in_cookies = False
        in_cookie = False
        while True:
            try:
                event, elem = iterator.next()
                tag = elem.tag
                if not in_cookies and 'cookies' == tag and 'start' == event:
                    in_cookies = True
                elif in_cookies and 'cookie' == tag and 'start' == event:
                    in_cookie = True
                elif in_cookie and 'raw' == tag and 'end' == event:
                    value = str(elem.text)
                    encoding = None
                    if elem.attrib.has_key('encoding'):
                        encoding = str(elem.attrib['encoding'])
                    if 'base64' == encoding:
                        value = value.decode('base64')
                    cookies = QNetworkCookie.parseCookies(value)
                    for cookie in cookies:
                        cookieList.append(cookie)
                elif 'cookies' == tag and 'end' == event:
                    in_cookies = False
                elif in_cookie and 'cookie' == tag and 'end' == event:
                    in_cookie = False

            except StopIteration:
                source.close()
                break

        return cookieList

    def handle_cookiesImportCookieJar_clicked(self):
        filename = QFileDialog.getOpenFileName(None, "Import Cookies", "", "XML File (*.xml);;BZ2 XML File (*.xml.bz2)")
        if filename and str(filename):
            importCookieList = self.load_cookies_from_file(str(filename))
            cookieJar = self.framework.get_global_cookie_jar()
            # merge cookies
            cookieList = cookieJar.allCookies()
            for cookie in importCookieList:
                if cookie not in cookieList:
                    cookieList.append(cookie)

            cookieJar.setAllCookies(cookieList)
            self.populate_cookie_jar_tree()

    def handle_cookiesDelete_clicked(self):
        cookieJar = self.framework.get_global_cookie_jar()
        cookieList = cookieJar.allCookies()
        domain = str(self.mainWindow.cookiesCookieJarDomainEdit.text())
        name = str(self.mainWindow.cookiesCookieJarNameEdit.text())
        cookie = self.find_cookie_by_domain_and_name(cookieList, domain, name)
        if cookie is not None:
            index = cookieList.index(cookie)
            cookieList.pop(index)

        cookieJar.setAllCookies(cookieList)
        self.populate_cookie_jar_tree()

    def handle_cookiesSave_clicked(self):
        cookieJar = self.framework.get_global_cookie_jar()
        cookieList = cookieJar.allCookies()
        domain = str(self.mainWindow.cookiesCookieJarDomainEdit.text())
        name = str(self.mainWindow.cookiesCookieJarNameEdit.text())
        value = str(self.mainWindow.cookiesCookieJarValueEdit.text())
        if not (domain and name and value):
            return
        cookie = self.find_cookie_by_domain_and_name(cookieList, domain, name)
        if cookie is None:
            # new
            cookie = QNetworkCookie(name, value)
            index = -1
        else:
            index = cookieList.index(cookie)

        cookie.setName(name)
        cookie.setDomain(domain)
        cookie.setValue(value)
        cookie.setPath(str(self.mainWindow.cookiesCookieJarPathEdit.text()))
        if self.mainWindow.cookiesCookieJarSessionCookieCheckbox.isChecked():
            cookie.setExpirationDate(QDateTime())
        else:
            cookie.setExpirationDate(self.mainWindow.cookiesCookieJarExpiryEdit.dateTime())
        cookie.setSecure(self.mainWindow.cookiesCookieJarSecureCheckbox.isChecked())
        cookie.setHttpOnly(self.mainWindow.cookiesCookieJarHttpOnlyCheckbox.isChecked())

        if -1 == index:
            cookieList.append(cookie)
        else:
            cookieList[index] = cookie

        cookieJar.setAllCookies(cookieList)
        self.populate_cookie_jar_tree()

    def find_cookie_by_domain_and_name(self, cookieList, domain, name):
        for cookie in cookieList:
            if str(cookie.domain()) == domain and str(cookie.name()) == name:
                return cookie
        return None

    def populate_cookieJar_edit_fields(self, cookie):
        self.mainWindow.cookiesCookieJarDomainEdit.setText(str(cookie.domain()))
        self.mainWindow.cookiesCookieJarNameEdit.setText(str(cookie.name()))
        self.mainWindow.cookiesCookieJarValueEdit.setText(str(cookie.value()))
        self.mainWindow.cookiesCookieJarPathEdit.setText(str(cookie.path()))
        if cookie.isSessionCookie():
            self.mainWindow.cookiesCookieJarExpiryEdit.setDateTime(self.mainWindow.cookiesCookieJarExpiryEdit.dateTimeFromText(''))
        else:
            self.mainWindow.cookiesCookieJarExpiryEdit.setDateTime(cookie.expirationDate().toUTC())
        self.mainWindow.cookiesCookieJarSessionCookieCheckbox.setChecked(cookie.isSessionCookie())
        self.mainWindow.cookiesCookieJarHttpOnlyCheckbox.setChecked(cookie.isHttpOnly())
        self.mainWindow.cookiesCookieJarSecureCheckbox.setChecked(cookie.isSecure())

    def clear_cookieJar_edit_fields(self, domain):
        self.mainWindow.cookiesCookieJarDomainEdit.setText(str(domain))
        self.mainWindow.cookiesCookieJarNameEdit.setText('')
        self.mainWindow.cookiesCookieJarValueEdit.setText('')
        self.mainWindow.cookiesCookieJarPathEdit.setText('')
        self.mainWindow.cookiesCookieJarExpiryEdit.setDateTime(self.mainWindow.cookiesCookieJarExpiryEdit.dateTimeFromText(''))
        self.mainWindow.cookiesCookieJarExpiryEdit.clear()
        self.mainWindow.cookiesCookieJarSessionCookieCheckbox.setChecked(False)
        self.mainWindow.cookiesCookieJarHttpOnlyCheckbox.setChecked(False)
        self.mainWindow.cookiesCookieJarSecureCheckbox.setChecked(False)

    def populate_cookie_jar_tree(self):
        cookieJar = self.framework.get_global_cookie_jar()
        cookieList = cookieJar.allCookies()
        self.mainWindow.cookiesCookieJarTreeWidget.clear()
        for cookie in cookieList:
            domain = str(cookie.domain())
            domainItems = self.mainWindow.cookiesCookieJarTreeWidget.findItems(domain, Qt.MatchExactly)
            if len(domainItems) > 0:
                # append
                parentItem = domainItems[-1]
            else:
                parentItem = QTreeWidgetItem([
                        domain,
                        ''
                        ])
                self.mainWindow.cookiesCookieJarTreeWidget.addTopLevelItem(parentItem)

            item = QTreeWidgetItem([
                    str(cookie.domain()),
                    str(cookie.name()),
                    str(cookie.value()),
                    str(cookie.path()),
                    str(cookie.expirationDate().toUTC().toString('MM/dd/yyyy hh:mm:ss')),
                    str(cookie.isSessionCookie()),
                    str(cookie.isHttpOnly()),
                    str(cookie.isSecure()),
                    ])

            parentItem.addChild(item)

    def populate_local_storage_tree(self):
        self.mainWindow.cookiesLocalStorageTreeWidget.clear()
        localstorage = self.localStorage.read_storage()
        for domain in localstorage.keys():
            domainItems = self.mainWindow.cookiesLocalStorageTreeWidget.findItems(domain, Qt.MatchExactly)
            if len(domainItems) > 0:
                # append
                parentItem = domainItems[-1]
            else:
                parentItem = QTreeWidgetItem([
                        domain,
                        '',
                        ''
                        ])
                self.mainWindow.cookiesLocalStorageTreeWidget.addTopLevelItem(parentItem)
            for name, value, filename in localstorage[domain]:
                item = QTreeWidgetItem([
                        str(domain),
                        str(name),
                        str(value),
                        ])
                parentItem.addChild(item)
                
    def handle_localStorageTreeWidget_itemClicked(self, item):
        domain = str(item.text(0))
        name = str(item.text(1))
        value = str(item.text(2))
        if domain and name:
            self.populate_localStorage_edit_fields(domain, name, value)
        else:
            self.clear_localStorage_edit_fields(domain)

    def handle_localStorageSave_clicked(self):
        domain = str(self.mainWindow.cookiesLocalStorageDomainEdit.text())
        name = str(self.mainWindow.cookiesLocalStorageNameEdit.text())
        value = str(self.mainWindow.cookiesLocalStorageValueEdit.text())
        if (domain and name):
            self.localStorage.update_storage_entry(domain, name, value)
            self.populate_local_storage_tree()

    def handle_localStorageDelete_clicked(self):
        domain = str(self.mainWindow.cookiesLocalStorageDomainEdit.text())
        name = str(self.mainWindow.cookiesLocalStorageNameEdit.text())
        if domain and name:
            self.localStorage.delete_storage_entry(domain, name)
            self.populate_local_storage_tree()

    def clear_localStorage_edit_fields(self, domain):
        self.mainWindow.cookiesLocalStorageDomainEdit.setText(str(domain))
        self.mainWindow.cookiesLocalStorageNameEdit.setText('')
        self.mainWindow.cookiesLocalStorageValueEdit.setText('')

    def populate_localStorage_edit_fields(self, domain, name, value):
        self.mainWindow.cookiesLocalStorageDomainEdit.setText(str(domain))
        self.mainWindow.cookiesLocalStorageNameEdit.setText(str(name))
        self.mainWindow.cookiesLocalStorageValueEdit.setText(str(value))

    def populate_flash_cookies_tree(self):
        self.mainWindow.cookiesFlashCookiesTreeWidget.clear()
        flashcookies = self.flashCookies.read_flashcookies()
        for domain in flashcookies.keys():
            domainItems = self.mainWindow.cookiesFlashCookiesTreeWidget.findItems(domain, Qt.MatchExactly)
            if len(domainItems) > 0:
                # append
                parentItem = domainItems[-1]
            else:
                parentItem = QTreeWidgetItem([
                        domain,
                        '',
                        ''
                        ])
                self.mainWindow.cookiesFlashCookiesTreeWidget.addTopLevelItem(parentItem)
            for element in flashcookies[domain]:
                item = QTreeWidgetItem([
                        domain,
                        str(element.name),
                        '',
                        ])
                parentItem.addChild(item)
                self.add_flash_name_value_item(item, domain, element)

    def add_flash_name_value_item(self, parentItem, domain, element):
        if isinstance(element, dict):
            for name in element.keys():
                value = element[name]
                if isinstance(value, dict):
                    item = QTreeWidgetItem([
                            '',
                            str(name),
                            '',
                            ])
                    parentItem.addChild(item)
                    self.add_flash_name_value_item(item, domain, value)
                else:
                    try:
                        svalue = str(value)
                    except UnicodeEncodeError:
                        svalue = repr(value)

                    item = QTreeWidgetItem([
                            '',
                            str(name),
                            svalue,
                            ])
                    parentItem.addChild(item)
            


        
