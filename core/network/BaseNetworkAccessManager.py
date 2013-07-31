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

        self.__use_proxy = False

        self.setProxy(QtNetwork.QNetworkProxy())
#        QObject.connect(self, SIGNAL('authenticationRequired(QNetworkReply *, QAuthenticator *)'), self.handle_authenticationRequired)
        self.authenticationRequired.connect(self.handle_authenticationRequired)

        self.framework.subscribe_database_events(self.__db_attach, self.__db_detach)
        self.framework.subscribe_raft_config_updated(self.__handle_raft_config_updated)

    def __db_attach(self):
        self.__proxy = {}
        self.__proxy['host'] = self.framework.get_raft_config_value('proxy_host', str)
        self.__proxy['port'] = self.framework.get_raft_config_value('proxy_port', int)
        self.__proxy['username'] = self.framework.get_raft_config_value('proxy_username', str)
        self.__proxy['password'] = self.framework.get_raft_config_value('proxy_password', str)
        self.__proxy['type'] = self.framework.get_raft_config_value('proxy_type', str)
        self.__use_proxy = self.framework.get_raft_config_value('use_proxy', bool)
        self.__setup_network_proxy()

    def __db_detach(self):
        pass

    def __handle_raft_config_updated(self, name, value):
        config_name = name
        new_value = value
        if config_name in ('proxy_host', 'proxy_username', 'proxy_password', 'proxy_type'):
            conf = config_name[6:] # skip proxy_
            if new_value != self.__proxy[conf]:
                self.__proxy[conf] = new_value
                self.__setup_network_proxy()
        elif 'proxy_port' == config_name:
            if new_value != str(self.__proxy['port']):
                try:
                    self.__proxy['port'] = int(new_value)
                    self.__setup_network_proxy()
                except ValueError:
                    pass
        elif 'use_proxy' == config_name:
            self.__use_proxy = bool(value)
            self.__setup_network_proxy()

    def __setup_network_proxy(self):
        proxy = self.proxy()
        if self.__use_proxy:
            proxy.setHostName(self.__proxy['host'])
            proxy.setPort(self.__proxy['port'])
            proxy.setUser(self.__proxy['username'])
            proxy.setPassword(self.__proxy['password'])
            if 'socks5' == self.__proxy['type']:
                proxy.setType(QtNetwork.QNetworkProxy.Socks5Proxy)
            else:
                proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
        else:
            proxy.setType(QtNetwork.QNetworkProxy.NoProxy)

        self.setProxy(proxy)

        if False:
            # TODO: should specify capabilities?
            proxy = self.proxy()
            for name, value in (('Tunneling', QtNetwork.QNetworkProxy.TunnelingCapability),
                                ('ListeningCapability', QtNetwork.QNetworkProxy.ListeningCapability),
                                ('UdpTunnelingCapability', QtNetwork.QNetworkProxy.UdpTunnelingCapability),
                                ('CachingCapability', QtNetwork.QNetworkProxy.CachingCapability),
                                ('HostNameLookupCapability', QtNetwork.QNetworkProxy.HostNameLookupCapability),):
                print(name, (int(proxy.capabilities()))&value)


    def handle_authenticationRequired(self, reply, authenticator):
        print(('authenticationRequired', reply, authenticator))
