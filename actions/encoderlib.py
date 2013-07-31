#
# This is the encoding / decoding functions collection for RAFT
#
# Authors:
#         Nathan Hamiel (nathan{at}neohaxor{dot}org)
#         Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2013 RAFT Team
# Copyright (c) 2010 Nathan Hamiel
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

import urllib.request, urllib.parse, urllib.error
import base64
import hashlib
import cgi
import html
import io
import zlib
import decimal
import re
from xml.sax.saxutils import unescape
from xml.sax.saxutils import escape
from codecs import getencoder, getdecoder
import binascii
from io import BytesIO, StringIO

###################
# Encoder section #
###################

_escape_map_full = {ord('&'): '&amp;', ord('<'): '&lt;', ord('>'): '&gt;',
                    ord('"'): '&quot;', ord('\''): '&#x27;'}

def url_encode(encvalue):
    """ URL encode the specifed value. Example Format: Hello%20World """
    
    try:
        encoded_value = urllib.parse.quote(encvalue)
    except:
        encoded_value = "There was a problem with the specified value"
    return(encoded_value)
    
def full_url_encode(encvalue):
    """ Full URL Hex encode the specified value.
    Example Format: %48%65%6c%6c%6f%20%57%6f%72%6c%64 """
    
    hexval = ""

    if isinstance(encvalue, bytes):
        for item in encvalue:
            val = '%%%02x' % item
            hexval += val
    else:
        for item in encvalue:
            val = '%%%02x' % ord(item)
            hexval += val
        
    return(hexval)

def base64_encode(encvalue):
    """ Base64 encode the specified value. Example Format: SGVsbG8gV29ybGQ= """
    
    try:
        if isinstance(encvalue, bytes):
            basedata = base64.b64encode(encvalue)
        else:
            basedata = base64.b64encode(bytes(encvalue, encoding="utf-8"))
    except:
        basedata = ""
    
    return(basedata.decode("utf-8"))

def html_entity_encode(encvalue):
    """ HTML Entity encoding using the CGI module escaping with quote """
    
    encoded = ''
    for c in encvalue:
        if not isinstance(c, int):
            c = ord(c)
        if c in _escape_map_full:
            encoded += _escape_map_full[c]
        elif 31 < c < 127:
            encoded += '%c' % (c)
        else:
            encoded += '&#x%02X;' % (c)
    
    return(encoded)

    
def hex_encode(encvalue):
    """ Encode value to Hex. Example Format: 48656c6c6f2576f726c64"""
    
    if isinstance(encvalue, bytes):
        hexval = binascii.b2a_hex(encvalue).decode('ascii')
    else:
        hexval = ''
        for item in encvalue:
            hexval += '%02x' % (ord(item))

    return hexval

def hexadecimal_escape(encvalue):
    """ Encode as hexadecimal escaped value: xss = \x78\x73\x73 """
    hexval = ""
    if isinstance(encvalue, bytes):
        for item in encvalue:
            hexval += '\\x%02x' % (item)
    else:
        for item in encvalue:
            hexval += '\\x%02x' % (ord(item))
    return(hexval)

def octal_escape(encvalue):
    """ Encode as octal escaped value: xss = \x78\x73\x73 """
    octval = ""
    if isinstance(encvalue, bytes):
        for item in encvalue:
            octval += '\\%03o' % (item)
    else:
        for item in encvalue:
            octval += '\\%03o' % (ord(item))
        
    return(octval)

def hex_entity_encode(encvalue):
    """ Encode value to a Hex entitiy. Example Format: &#x48;&#x65;&#x6c;&#x6c;&#x6f;"""
    
    hexval = ""
    if isinstance(encvalue, bytes):
        for item in encvalue:
            hexval += '&#x%02x;' % (item)
    else:
        for item in encvalue:
            hexval += '&#x%02x;' % (ord(item))
        
    return(hexval)
    
def unicode_encode(encvalue):
    """ Unicode encode the specified value in the %u00 format. Example:
    %u0048%u0065%u006c%u006c%u006f%u0020%u0057%u006f%u0072%u006c%u0064 """
    
    hexval = ""

    if isinstance(encvalue, bytes):
        for item in encvalue:
            hexval += '%%u%04X' % (item)
    else:
        for item in encvalue:
            hexval += '%%u%04X' % (ord(item))
        
    return(hexval)
    
def escape_xml(encvalue):
    """ Escape the specified HTML/XML value. Example Format: Hello&amp;World """
    
    if isinstance(encvalue, bytes):
        escaped = ''
        for c in encvalue:
            if 31 < c < 127:
                escaped += escape(chr(c), {"'": "&apos;", '"': "&quot;"})
            else:
                escaped += '&#x%02x;' % (c)
    else:
        escaped = escape(encvalue, {"'": "&apos;", '"': "&quot;"})
    
    return(escaped)
    
def md5_hash(encvalue):
    """ md5 hash the specified value.
    Example Format: b10a8db164e0754105b7a99be72e3fe5"""
    
    hashdata = hashlib.md5()
    if isinstance(encvalue, bytes):
        hashdata.update(encvalue)
    else:
        hashdata.update(encvalue.encode("utf-8"))
    
    return(hashdata.hexdigest())
    
def sha1_hash(encvalue):
    """ sha1 hash the specified value.
    Example Format: 0a4d55a8d778e5022fab701977c5d840bbc486d0 """
    
    hashdata = hashlib.sha1()
    if isinstance(encvalue, bytes):
        hashdata.update(encvalue)
    else:
        hashdata.update(encvalue.encode("utf-8"))
    
    return(hashdata.hexdigest())
    
def sqlchar_encode(encvalue):
    """ SQL char encode the specified value.
    Example Format: CHAR(72)+CHAR(101)+CHAR(108)+CHAR(108)+CHAR(111)"""
    
    charstring = ""

    if isinstance(encvalue, bytes):
        for item in encvalue:
            val = "CHAR(" + str(item) + ")+"
            charstring += val
    else:
        for item in encvalue:
            val = "CHAR(" + str(ord(item)) + ")+"
            charstring += val
    
    return(charstring.rstrip("+"))
    
####
# oraclechr_encode not tested yet, but should work
####
def oraclechr_encode(encvalue):
    """ Oracle chr encode the specified value. """
    
    charstring = ""
    
    if isinstance(encvalue, bytes):
        for item in encvalue:
            val = "chr(" + str(item) + ")||"
            charstring += val
    else:
        for item in encvalue:
            val = "chr(" + str(ord(item)) + ")||"
            charstring += val
        
    return(charstring.rstrip("||"))

def decimal_convert(encvalue):
    """ Convert input to decimal value.
    Example Format: 721011081081113287111114108100 """
    
    decvalue = ""
    
    if isinstance(encvalue, bytes):
        for item in encvalue:
            decvalue += str(item)
    else:
        for item in encvalue:
            decvalue += str(ord(item))

    return(decvalue)

def decimal_entity_encode(encvalue):
    """ Convert input to a decimal entity.
    Example Format: &#72;&#101;&#108;&#108;&#111;&#32;&#87;&#111;&#114;&#108;&#100; """
    
    decvalue = ""
    
    if isinstance(encvalue, bytes):
        for item in encvalue:
            decvalue += "&#" + str(item) +";"
    else:
        for item in encvalue:
            decvalue += "&#" + str(ord(item)) +";"
        
    return(decvalue)

def rot13_encode(encvalue):
    """ Perform ROT13 encoding on the specified value.
    Example Format: Uryyb Jbeyq """
    
    encoder = getencoder("rot-13")
    if isinstance(encvalue, bytes):
        rot13 = encoder(encvalue.decode('ascii', 'ignore')) [0]
    else:
        rot13 = encoder(encvalue) [0]
    
    return(rot13)

def _int2bits(val, width):
    result = ''
    for i in range(width, 0, -1):
        if 0 != (val & (1 << (i-1))):
            result += '1'
        else:
            result += '0'
    return result

def _bits2int(val):
    result = 0
    for c in val:
        result <<= 1
        if '1' == c:
            result += 1
    return result

def _utf7_encode(encvalue, padbit):
    nonalphanum = re.compile(r'[^a-zA-Z0-9]')
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

    result = ''
    if isinstance(encvalue, bytes):
        # TODO: this may be lossy
        raw = encvalue.decode('utf-8', 'ignore').encode('utf-16be')
    else:
        raw = encvalue.encode('utf-16be')

    for i in range(0, int(len(raw)/2)):
        ch1, ch2 = raw[i*2], raw[i*2+1]
        if 0 == ch1 and ord('+') == ch2:
            result += '+-'
        elif 0 != ch1 or nonalphanum.match(chr(ch2)):
            bits = _int2bits(ch1, 8) + _int2bits(ch2, 8)
            bits += padbit * (6 - int(len(bits)%6))
            result += '+'
            for offset in range(0, int(len(bits)/6)):
                val = _bits2int(bits[offset*6:offset*6+6])
                result += alphabet[val]
            result += '-'
        else:
            result += chr(ch2)

    return result

def utf7_encode(encvalue):
    """ Encode non-alphanumerics as UTF-7 """
    return _utf7_encode(encvalue, '0')

def utf7_malformed_encode(encvalue):
    """ Encode non-alphanumerics as UTF-7 with bad padding """
    return _utf7_encode(encvalue, '1')

###################
# Decoder section #
###################

def url_decode(decvalue):
    """ URL Decode the specified value. Example Format: Hello%20World """
    
    # returnval = urllib.unquote(decvalue.decode)
    returnval = urllib.parse.unquote(decvalue)
    
    return(returnval)
    
def fullurl_decode(decvalue):
    """ Full URL decode the specified value.
    Example Format: %48%65%6c%6c%6f%20%57%6f%72%6c%64 """

    return unified_url_decode(decvalue)
    
def base64_decode(decvalue):
    """ Base64 decode the specified value.
    Example Format: SGVsbG8gV29ybGQ= """
    
    msg = """ There was an error. Most likely this isn't a valid Base64 value
    and Python choked on it """
    
    try:
        # base64dec = decvalue.decode("Base64")
        base64dec = base64.b64decode(bytes(decvalue, encoding="utf-8"))
        return(base64dec)
    except:
        return(msg)

def hex_decode(decvalue):
    """ Hex decode the specified value.
    Example Format: 48656c6c6f2576f726c64 """
    
    msg = """ There was an error, perhaps an invalid length for the hex
    value """
    
    try:
        decodeval = binascii.a2b_hex(decvalue)
    except TypeError:
        # fallback, decode what is possible
        re_hex = re.compile(r'([0-9a-f]{2})', re.I)
        decodeval = re_hex.sub(lambda m: binascii.a2b_hex(m.group(1)), decvalue)

    return(decodeval)

def hexadecimal_unescape(decvalue):
    """ Hex unescape the specified value.
    Example Format: \x48\x65\x6c\x6c\x6f\x25\x76\xf7\x26\xc64 """

    re_hex = re.compile(r'(\\x[0-9a-f]{2})', re.I)
    items = re_hex.split(decvalue)
    bio = BytesIO()
    for item in items:
        if 4 == len(item) and item.startswith('\\x'):
            bio.write(int(item[2:], 16).to_bytes(1, 'big'))
        else:
            bio.write(item.encode('utf-8', 'ignore'))
        
    decodeval = bio.getvalue()
    return (decodeval)

def octal_unescape(decvalue):
    # TODO: this could be better
    re_oct = re.compile(r'\\(0[0-7]{3}|[0-7]{3})')
    decodeval = re_oct.sub(lambda m: '%c' % int(m.group(1), 8), decvalue)
    return (decodeval)
        
def hexentity_decode(decvalue):
    """ Hex entity decode the specified value.
    Example Format: &#x48;&#x65;&#x6c;&#x6c;&#x6f; """
    
    charval = ""
    splithex = decvalue.split(";")
    
    for item in splithex:
        # Necessary because split creates an empty "" that tries to be
        # converted with int()
        if item != "":
            hexcon = item.replace("&#", "0")
            charcon = chr(int(hexcon, 16))
            charval += charcon
        else:
            pass
    
    return(charval)

def unescape_xml(decvalue):
    """ Unescape the specified HTML or XML value: Hello&amp;World"""
    
    unescaped = unescape(decvalue, {"&apos;": "'", "&quot;": '"'})
    
    return(unescaped)

def unicode_decode(decvalue):    
    """ Unicode decode the specified value %u00 format. 
    Example Format: %u0048%u0065%u006c%u006c%u006f%u0020%u0057%u006f%u0072%u006c%u0064 """

    return unified_url_decode(decvalue)

def unified_url_decode(decvalue):
    """ Handle both %XX and %uXXXX encoded types in URL"""

    charval = b''

    re_unicode = re.compile(r'((?:%[0-9a-f]{2})|(?:%u[0-9a-f]{4}))', re.I)
    re_is_hex = re.compile(r'^[0-9a-f]+$', re.I)
    items = re_unicode.split(decvalue)
    bio = BytesIO()
    for item in items:
        if 6 == len(item) and item.startswith('%u') and re_is_hex.match(item[2:]):
            a, b = item[2:4], item[4:]
            if '00' == a:
                bio.write(int(b, 16).to_bytes(1, 'big'))
            else:
                bio.write(int(item[2:], 16).to_bytes(2, 'big'))
        elif 3 == len(item) and item.startswith('%') and re_is_hex.match(item[1:]):
            bio.write(int(item[1:], 16).to_bytes(1, 'big'))
        else:
            bio.write(item.encode('utf-8', 'ignore'))

    charval = bio.getvalue()
    return(charval)
    
def rot13_decode(decvalue):
    """ ROT13 decode the specified value. Example Format: Uryyb Jbeyq  """
    
    decoder = getdecoder("rot-13")
    rot13 = decoder(decvalue) [0]
    
    return(rot13)

def utf7_decode(decvalue):
    """ UTF-7 decode value including values with bad padding """
    result = b''
    i = 0
    valuelen = len(decvalue)
    while i < valuelen:
        ch = decvalue[i]
        i += 1
        if '+' == ch:
            if '-' == decvalue[i]:
                result += b'+'
            else:
                tmp = ''
                while '-' != decvalue[i]:
                    tmp += decvalue[i]
                    i += 1
                tmp += '=' * (4 - (len(tmp)%4))
                val = base64.b64decode(bytes(tmp, 'ascii'))
                for j in range(0, int(len(val)/2)):
                    result += val[j*2:j*2+2].decode('utf-16be').encode('utf-8','ignore')
            i += 1
        else:
            result += bytes(ch, 'ascii')

    return(result)

############################################
# Items for interface with the Decoder tab #
############################################

def encode_values(encode_value, encode_method):
    """ Encode the values from the encodeEdit """

    value = ""
    
    if encode_method == "URL":
        value = url_encode(encode_value)
    elif encode_method == "Full URL":
        value = full_url_encode(encode_value)
    elif encode_method == "Base64":
        value = base64_encode(encode_value)
    elif encode_method == "HTML Entity":
        value = html_entity_encode(encode_value)
    elif encode_method == "Hex":
        value = hex_encode(encode_value)
    elif encode_method == "Hex Entity":
        value = hex_entity_encode(encode_value)
    elif encode_method == "Hexadecimal Escape":
        value = hexadecimal_escape(encode_value)
    elif encode_method == "Octal Escape":
        value = octal_escape(encode_value)
    elif encode_method == "MD5 Hash":
        value = md5_hash(encode_value)
    elif encode_method == "SHA1 Hash":
        value = sha1_hash(encode_value)
    elif encode_method == "SQL CHAR String":
        value = sqlchar_encode(encode_value)
    elif encode_method == "Oracle chr String":
        value = oraclechr_encode(encode_value)
    elif encode_method == "Unicode %u00":
        value = unicode_encode(encode_value)
    elif encode_method == "Escape HTML/XML":
        value = escape_xml(encode_value)
    elif encode_method == "Decimal":
        value = decimal_convert(encode_value)
    elif encode_method == "Decimal Entity":
        value = decimal_entity_encode(encode_value)
    elif encode_method == "ROT13":
        value = rot13_encode(encode_value)
    elif encode_method == "UTF-7":
        value = utf7_encode(encode_value)
    elif encode_method == "UTF-7 (Malformed)":
        value = utf7_malformed_encode(encode_value)
        
    return(value)
    
def wrap_encode(encode_value, wrap_value):
    """ Wrap the encode chars """

   
    if wrap_value == "<script></script>":
        value = "<script>" + encode_value + "</script>"
    elif wrap_value == "<ScRiPt></ScRiPt>":
        value = "<ScRiPt>" + encode_value + "</ScRiPt>"
    elif wrap_value == "alert(...)":
        value = "alert(" + encode_value + ")"
    elif wrap_value == '"Javascript:..."':
        value = '"javascript:' + encode_value + '"'
    elif wrap_value == '<img src="..."':
        value = '<img src="' + encode_value + '">'
        
    return(value)
    
def decode_values(decode_value, decode_method):
    """ Decode the values from the decodeEdit """

    value = ""
    
    if decode_method == "URL":
        value = url_decode(decode_value)
    elif decode_method == "Full URL":
        value = fullurl_decode(decode_value)
    elif decode_method == "Base64":
        value = base64_decode(decode_value)
    elif decode_method == "Hex":
        value = hex_decode(decode_value)
    elif decode_method == "Hex Entity":
        value = hexentity_decode(decode_value)
    elif decode_method == "Hexadecimal Unescape":
        value = hexadecimal_unescape(decode_value)
    elif decode_method == "Octal Unescape":
        value = octal_unescape(decode_value)
    elif decode_method == "Unescape HTML/XML":
        value = unescape_xml(decode_value)
    elif decode_method == "Unicode %u00":
        value = unicode_decode(decode_value)
    elif decode_method == "ROT13":
        value = rot13_decode(decode_value)
    elif decode_method == "UTF-7":
        value = utf7_decode(decode_value)
    else:
        print(('unimplemented decode method,', decode_method))

    return(value)
    
def wrap_decode(decode_value, wrap_value):
    """ Wrap the Decode Values """

    
    if wrap_value == "<script></script>":
        value = "<script>" + decode_value + "</script>"
    elif wrap_value == "<ScRiPt></ScRiPt>":
        value = "<ScRiPt>" + decode_value + "</ScRiPt>"
    elif wrap_value == "alert(...)":
        value = "alert(" + decode_value + ")"
    elif wrap_value == '"javascript:..."':
        value = '"javascript:' + decode_value + '"'
    elif wrap_value == '<img src="..."':
        value = '<img src="' + decode_value + '">'

    return(value)

if '__main__' == __name__:
    # test code
    values = (
    b'test->abcd;1234&x=1\x01\x02\'\"',
     'test->abcd;1234&x=1\x01\x02\'\"'
    )
    funcs = (
        (encoderlib.url_encode, encoderlib.url_decode),
        (encoderlib.full_url_encode, encoderlib.fullurl_decode),
        (encoderlib.base64_encode, encoderlib.base64_decode),
        (encoderlib.html_entity_encode, encoderlib.unescape_xml),
        (encoderlib.hex_encode, encoderlib.hex_decode),
        (encoderlib.hexadecimal_escape, encoderlib.hexadecimal_unescape),
        (encoderlib.octal_escape, encoderlib.octal_unescape),
        (encoderlib.hex_entity_encode, encoderlib.hexentity_decode),
        (encoderlib.unicode_encode, encoderlib.unicode_decode),
        (encoderlib.escape_xml, None),
        (encoderlib.md5_hash, None),
        (encoderlib.sha1_hash, None),
        (encoderlib.sqlchar_encode, None),
        (encoderlib.oraclechr_encode, None),
        (encoderlib.decimal_convert, None),
        (encoderlib.decimal_entity_encode, None),
        (encoderlib.rot13_encode, encoderlib.rot13_decode),
        (encoderlib.utf7_encode, encoderlib.utf7_decode),
        (encoderlib.utf7_malformed_encode, encoderlib.utf7_decode),
    )
    for encfunc, decfunc in funcs:
        for value in values:
            e = encfunc(value)
            if decfunc:
                b = decfunc(e)
                if isinstance(b, bytes):
                    d = b.decode('utf-8', 'ignore')
                else:
                    d = b
                print((e, d))
                if (value != b) and (value != d):
                    print (encfunc, decfunc)
                    print ('*' * 80)
                    print(value)
                    print(d)
                    print ('*' * 80)
            else:
                print(e)
