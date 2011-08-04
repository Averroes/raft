#
# Author: Seth Law
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
import re

from ..AbstractAnalyzer import AbstractAnalyzer


class FindInsecureCookies(AbstractAnalyzer):
    
    #Class variables shared across all instances
    SetCookieRegex = re.compile("set-cookie\:\s(\S*?=\S*?);\s(.*)",re.I)
    SecureRegex = re.compile("secure",re.I)
    HttpOnlyRegex = re.compile("httponly",re.I)
    HttpsRegex = re.compile("https://",re.I)
    PathRegex = re.compile("path=/;{0,1}\s",re.I)
    UrlPathRegex = re.compile("https{0,1}:\/\/.*\/(\S+)")
    outputSecureHeader = 'Cookies not marked as "secure"'
    notSecureText = "If the 'secure' flag is included in the HTTP set-cookie response header, the cookie will only be sent with a request when the browser is communicating using HTTPS."
    notSecure = {}
    outputHttpHeader = 'Cookies not marked as "httponly"'
    notHttpOnlyText = "If the HttpOnly flag (optional) is included in the HTTP response header, the cookie cannot be accessed through client side script (again if the browser supports this flag). As a result, even if a cross-site scripting (XSS) flaw exists, and a user accidentally accesses a link that exploits this flaw, the browser (primarily Internet Explorer) will not reveal the cookie to a third party. - https://www.owasp.org/index.php/HttpOnly"
    notHttpOnly = {}
    outputPathRestrictedHeader = 'Cookies not path restricted'
    notPathRestrictedText = "If a cookie is not path restricted, separate application within the same host may access unauthorized cookies."
    notPathRestricted = {}
    cookies = {}
    
    def __init__(self):
        self.desc="Identifies Cookies that are set using insecure parameters."
        self.friendlyname="Find Insecure Cookies"
    
    def analyzeTransaction(self, target, results):
        responseHeaders=target.responseHeaders
        host = target.requestHost
        url = target.responseUrl
        
        outputSecure = ''
        outputHttp = ''
        outputPR = ''
        for found in FindInsecureCookies.SetCookieRegex.finditer(responseHeaders):
            cookie = found.group(1)
            params = found.group(2)
            (name,value) = re.split("=",cookie,1)
        
            try:
                self.cookies[host]
            except:
                self.cookies[host] = {}
            try:
                self.cookies[host][name]
            except:
                self.cookies[host][name] = []
            self.cookies[host][name].append(value)
                
            if ((FindInsecureCookies.SecureRegex.search(params) == None) and (self.HttpsRegex.search(url)) and (len(value) > 0)):
                try:
                    self.notSecure[host]
                except:
                    self.notSecure[host] = {}
                    
                try:
                    self.notSecure[host][name]
                except:
                    self.notSecure[host][name] = 0
                self.notSecure[host][name] += 1
                outputSecure += "%s " % name
                    
            if (FindInsecureCookies.HttpOnlyRegex.search(params) == None and (len(value) > 0)):
                try:
                    self.notHttpOnly[host]
                except:
                    self.notHttpOnly[host] = {}
                        
                try:
                    self.notHttpOnly[host][name]
                except:
                    self.notHttpOnly[host][name] = 0
                self.notHttpOnly[host][name] += 1
                outputHttp += "%s " % name
                    
                
            if ((FindInsecureCookies.PathRegex.search(params) != None) and (self.UrlPathRegex.search(url) != None) and (len(value) > 0)):
                try:
                    self.notPathRestricted[host]
                except:
                    self.notPathRestricted[host] = {}
                        
                try:
                    self.notPathRestricted[host][name]
                except:
                    self.notPathRestricted[host][name] = 0
                self.notPathRestricted[host][name] += 1
                outputPR += "%s " % name
                
                
        dataoutput = {}
        if len(outputSecure) > 0:
            dataoutput[self.outputSecureHeader] = outputSecure
            
        if len(outputHttp) > 0:
            dataoutput[self.outputHttpHeader] = outputHttp
            
        if len(outputPR) > 0:
            dataoutput[self.outputPathRestrictedHeader] = outputPR
        
        if len(dataoutput) > 0:
            #print found.group(0).__class__
            results.addPageResult(pageid=target.responseId, 
                                url=target.responseUrl,
                                type=self.friendlyname,
                                desc=self.desc,
                                data=dataoutput,
                                span=None,
                                highlightdata=found.group(0))

    def postanalysis(self,results):
        outputSecureValue = ""
        for h in self.notSecure.iterkeys():
            outputSecureValue += " %s (" % h
            first = True
            for v in self.notSecure[h].iterkeys():
                if not first:
                    outputSecureValue += ", "
                else:
                    first = False
                outputSecureValue += "%s" % v
            outputSecureValue += ")"
            
            results.addOverallResult(type=self.friendlyname,
                                     desc=self.desc,
                                     data={self.outputSecureHeader:outputSecureValue},
                                     span=None,
                                     certainty=None,
                                     context=h
                                     )

        outputHttpValue = ""
        for h in self.notHttpOnly.iterkeys():
            outputHttpValue += " %s (" % h
            first = True
            for v in self.notHttpOnly[h].iterkeys():
                if not first:
                    outputHttpValue += ", "
                else:
                    first = False
                outputHttpValue += "%s" % v
            outputHttpValue += ")"
               
            results.addOverallResult(type=self.friendlyname,
                                     desc=self.desc,
                                     data={self.outputHttpHeader:outputHttpValue},
                                     span=None,
                                     certainty=None,
                                     context=h
                                     )
        
        for cookie in self.OWASP_Cookie_Map:
            cookieRE = re.compile(cookie,re.I)
            for h in self.cookies.iterkeys():
                for c in self.cookies[h].iterkeys():
                    if cookieRE.search(c):
                        results.addOverallResult(type='OWASP Cookie Database',
                                     desc='Cookies identified in the OWASP Cookie Database (https://www.owasp.org/index.php/Category:OWASP_Cookies_Database) may reveal architecture information about the application and/or web server.',
                                     data={cookie:self.OWASP_Cookie_Map[cookie]},
                                     span=None,
                                     certainty=None,
                                     context=h
                                     )



    OWASP_Cookie_Map={
        'JSESSIONID': 'J2EE Application Server - Many appservers use this cookie including Claudio Resin, Jakarta Tomcat/JSERV, Macromedia Jrun',
        'ASPSESSIONID': 'Microsoft IIS 5.0 - Cookie name varies by site',
        'ASP.Net_SessionId': 'Microsoft IIS 6.0',
        'PHPSESSION': 'The PHP Group - PHP',
        'wiki18_session': 'MediaWiki 1.8 - Content Management Server - http://www.wikipedia.com/',
        'WebLogicSession': 'BEA Weblogic - J2EE Application Server',
        'BIGipServer': 'F5 BIG-IP Load Balancer - Used to mantain persistence based on original client when balancing to a farm. The cookie name contains the name of the web site being accessed as well as the protocol used.',
        'SERVERID': 'HAproxy Load Balancer - More information in the [ http://haproxy.1wt.eu/download/1.2/doc/architecture.txt Architecture documentation]',
        'SaneID': 'UNica NetTracker (formerly SANE NetTracker) - http://www.sane.com/ - A.B.C.D in the cookie value is the IP address of the client accessing the site',
        'ssuid': 'Vignette Content Manager',
        'vgnvisitor': 'Vignette Content Manager',
        'SESSION_ID': 'IBM Net.Commerce',
        'NSES40Session': 'Redhat - Netscape Enterprise Server 4.0',
        'iPlanetUserId': 'Sun iPlanet web server (discontinued) - A.B.C.D in the cookie value is the client\'s IP address',
        'gx_session_id': 'Sun Java System Application Server',
        'JROUTE': 'Sun Java System Application Server - Used by the load balancing module to determine the server backend',
        'RMID': 'RealMedia OpenAdStream 6.x Media Server',
        'Apache': 'Apache web server - http://www.paypal.com/ - A.B.C.D in the cookie value is the client\'s IP address',
        'CFID': 'Macromedia Coldfusion Application Server',
        'CFTOKEN': 'Macromedia Coldfusion Application Server',
        'CFGLOBALS': 'Macromedia Coldfusion Application Server',
        'RoxenUserID': 'Roxen Web Server',
        'JServSessionIdroot': 'Apache Foundation - ApacheJServ',
        'sesessionid': 'IBM WebSphere Application Server',
        'PD-S-SESSION-ID': 'IBM Tivoli Access Manager WebSeal (part of the IBM TAM for e-business) - 5.x, 6.x - Reverse authentication proxy',
        'PD_STATEFUL': 'IBM Tivoli Access Manager WebSeal (part of the IBM TAM for e-business) - 5.x, 6.x - Reverse authentication proxy',
        'WEBTRENDS_ID': 'WebTrends Tracking',
        '__utm': 'Google Urchin Tracking Module',
        'sc_id': 'Omniture http://2o7.net Tracking',
        's_sq': 'Omniture http://2o7.net Tracking',
        's_sess': 'Omniture http://2o7.net Tracking',
        's_vi_': 'Omniture http://2o7.net Tracking',
        'Mint': 'Shaun Inman - Mint - Tracking',
        'SS_X_CSINTERSESSIONID': 'FatWire OpenMarket/FatWire Content Server',
        'CSINTERSESSIONID':'FatWire OpenMarket/FatWire Content Server',
        '_sn': 'Siebel CRM Application',
        'BCSI-CSC': 'BlueCoat Proxy',
        'Ltpatoken': 'IBM WebSphere Application Server',
        'DomAuthSessID': 'IBM Lotus Domino Session-based authentication'    
    }
