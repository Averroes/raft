#
# This base network access manager that all others should derive from
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

from PyQt4 import QtNetwork
from PyQt4.QtCore import QObject, SIGNAL, QUrl, QIODevice, QByteArray

class BaseNetworkAccessManager(QtNetwork.QNetworkAccessManager):
    def __init__(self, framework):
        QtNetwork.QNetworkAccessManager.__init__(self)
        self.framework = framework

        self.__proxy_host = 'localhost'
        self.__proxy_port = 8080
        self.__use_proxy = False

        self.setProxy(QtNetwork.QNetworkProxy())
#        QObject.connect(self, SIGNAL('authenticationRequired(QNetworkReply *, QAuthenticator *)'), self.handle_authenticationRequired)
        self.authenticationRequired.connect(self.handle_authenticationRequired)

        self.framework.subscribe_database_events(self.__db_attach, self.__db_detach)
        self.framework.subscribe_raft_config_updated(self.__handle_raft_config_updated)

    def __db_attach(self):
        self.__proxy_host = self.framework.get_raft_config_value('proxy_host', str)
        self.__proxy_port = self.framework.get_raft_config_value('proxy_port', int)
        self.__use_proxy = self.framework.get_raft_config_value('use_proxy', bool)
        self.__setup_network_proxy()

    def __db_detach(self):
        pass

    def __handle_raft_config_updated(self, name, value):
        config_name = str(name)
        new_value = str(value)
        if 'proxy_host' == config_name:
            if new_value != self.__proxy_host:
                self.__proxy_host = new_value
                self.__setup_network_proxy()
        elif 'proxy_port' == config_name:
            if new_value != str(self.__proxy_port):
                try:
                    self.__proxy_port = int(new_value)
                    self.__setup_network_proxy()
                except ValueError:
                    pass
        elif 'use_proxy' == config_name:
            self.__use_proxy = bool(value.toBool())
            self.__setup_network_proxy()

    def __setup_network_proxy(self):
        proxy = self.proxy()
        if self.__use_proxy:
            proxy.setHostName(self.__proxy_host)
            proxy.setPort(self.__proxy_port)
            proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
        else:
            proxy.setType(QtNetwork.QNetworkProxy.NoProxy)

        self.setProxy(proxy)

#         proxy = self.proxy()
#         for name, value in (('Tunneling', QtNetwork.QNetworkProxy.TunnelingCapability),
#                             ('ListeningCapability', QtNetwork.QNetworkProxy.ListeningCapability),
#                             ('UdpTunnelingCapability', QtNetwork.QNetworkProxy.UdpTunnelingCapability),
#                             ('CachingCapability', QtNetwork.QNetworkProxy.CachingCapability),
#                             ('HostNameLookupCapability', QtNetwork.QNetworkProxy.HostNameLookupCapability),):
#             print(name, (int(proxy.capabilities()))&value)


    def handle_authenticationRequired(self, reply, authenticator):
        print('authenticationRequired', reply, authenticator)
