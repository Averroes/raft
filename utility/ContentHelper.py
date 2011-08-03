#
# This file contains content helper routines
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

def getContentType(contentType, data = ''):
    # TODO: implement
    return contentType

def getCharSet(contentType):
    # TODO : remove, deprecated ... use BaseExtractor instead
    charset = ''
    if contentType:
        lookup = 'charset='
        n = contentType.lower().find(lookup)
        if n > -1:
            charset = contentType[n+len(lookup):].strip()
    if not charset:
        charset = 'utf-8'
    return charset

def decodeBody(data, charset):
    try:
        bodyText = None
        try:
            bodyText = data.decode(charset)
        except UnicodeDecodeError:
            pass
        except UnicodeEncodeError:
            pass
        except LookupError:
            pass
        if bodyText is None:
            bodyText = data.decode('utf-8')
    except UnicodeDecodeError:
        # TODO: handle binary content ???
        bodyText = repr(data)[1:-1].replace('\\r', '').replace('\\n', '\n').replace('\\t', '\t')
    except UnicodeEncodeError:
        # TODO: handle binary content ???
        bodyText = repr(data)[1:-1].replace('\\r', '').replace('\\n', '\n').replace('\\t', '\t')

    return bodyText

def combineRaw(headers, data, charset = 'utf-8'):
    # TODO: this functionality needs to be at a higher level
    # TODO: expect ascii always?
    headersText = headers.decode('ascii', 'replace')
    if not (headersText.endswith('\r\n\r\n') or headersText.endswith('\n\n')):
        headersText += '\r\n'

    bodyText = decodeBody(data, charset)

    return (headersText, bodyText, headersText + bodyText)

