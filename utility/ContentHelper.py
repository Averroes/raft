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

import codecs
BOM_MAPPINGS = (
    (codecs.BOM_UTF32_BE,'utf-32-be'),
    (codecs.BOM_UTF32_LE,'utf-32-le'),
    (codecs.BOM_UTF16_BE,'utf-16-be'),
    (codecs.BOM_UTF16_LE,'utf-16-le'),
    (codecs.BOM_UTF32,'utf-32'), # TODO:
    (codecs.BOM_UTF16,'utf-16'), # TODO: 
    (codecs.BOM_UTF8,'utf-8'),
    )

def getContentType(contentType, data = ''):
    # TODO: implement
    return contentType

def getCharSet(contentType, default_charset = 'utf-8'):
    if isinstance(contentType, bytes):
        contentType = contentType.decode('utf-8', 'ignore')
    charset = ''
    if contentType:
        lookup = 'charset='
        n = contentType.lower().find(lookup)
        if n > -1:
            charset = contentType[n+len(lookup):].strip()
    if not charset:
        return default_charset
    else:
        return charset

def getContentTypeFromHeaders(headers, default_content_type = 'text/html'):
    lines = headers.splitlines()
    pos = 0
    content_type = None
    for line in lines:
        if b':' in line:
            name, value = [x.strip() for x in line.split(b':', 1)]
            if b'content-type' == name.lower():
                content_type = value
                break
    if not content_type:
        return default_content_type
    else:
        return content_type.decode('utf-8', 'ignore')

def decodeBody(data, charset):
    try:
        bodyText = None
        try:
            for bom, encoding in BOM_MAPPINGS:
                if data.startswith(bom): 
                    temp = data[len(bom):]
                    if temp.startswith(bom): # can happen
                        temp = temp[len(bom):]
                    bodyText = temp.decode(encoding, 'ignore') # TODO: is ignore best approach, or allow to error?
                    break

        except UnicodeDecodeError:
            pass
        except LookupError:
            pass
        if bodyText is None:
            bodyText = data.decode('utf-8')

        if '\0' in bodyText:
            bodyText = repr(bodyText)[1:-1].replace('\\r', '').replace('\\n', '\n').replace('\\t', '\t')
    except UnicodeDecodeError:
        # TODO: handle binary content ???
        bodyText = repr(data)[2:-1].replace('\\r', '').replace('\\n', '\n').replace('\\t', '\t')
    except UnicodeEncodeError:
        # TODO: handle binary content ???
        bodyText = repr(data)[2:-1].replace('\\r', '').replace('\\n', '\n').replace('\\t', '\t')

    return bodyText

def combineRaw(headers, data, charset = 'utf-8'):
    # TODO: this functionality needs to be at a higher level
    # TODO: expect ascii always?
    headersText = headers.decode('ascii', 'ignore')
    if not (headersText.endswith('\r\n\r\n') or headersText.endswith('\n\n')):
        headersText += '\r\n'

    bodyText = decodeBody(data, charset)

    return (headersText, bodyText, headersText + bodyText)

def convertBytesToDisplayText(b):
    # TODO: implement hex dump
    if bytes == type(b):
        try:
            s = b.decode('utf-8')
        except UnicodeDecodeError:
            s = repr(b)[2:-1].replace('\\r', '').replace('\\n', '\n').replace('\\t', '\t')
        return s
    else:
        return b
    
def getCombinedText(headers, data, content_type):
    charset = 'utf-8'
    if content_type:
        ct = content_type.lower() 
        n = ct.find('charset=')
        if n > 0:
            charset = ct[n+8:]
            if ';' in charset:
                charset, junk = charset.split(';',1)
    headersText, bodyText, combinedText = combineRaw(headers, data, charset)
    return combinedText
