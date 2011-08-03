#
# This is the encoding / decoding functions collection for RAFT
#
# Authors:
#         Nathan Hamiel (nathan{at}neohaxor{dot}org)
#         Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2011 RAFT Team
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

import urllib
import hashlib
import cgi
import StringIO
import zlib
import decimal
import re
from xml.sax.saxutils import unescape
from xml.sax.saxutils import escape

###################
# Encoder section #
###################

def url_encode(encvalue):
    """ URL encode the specifed value. Example Format: Hello%20World """
    
    try:
        encoded_value = urllib.quote(encvalue)
    except:
        encoded_value = "There was a problem with the specified value"
    return(encoded_value)
    
def full_url_encode(encvalue):
    """ Full URL Hex encode the specified value.
    Example Format: %48%65%6c%6c%6f%20%57%6f%72%6c%64 """
    
    hexval = ""
    
    for item in encvalue:
        val = hex(ord(item)).replace("0x", "%")
        hexval += val
        
    return(hexval)

def base64_encode(encvalue):
    """ Base64 encode the specified value. Example Format: SGVsbG8gV29ybGQ= """
    
    try:
        basedata = encvalue.encode("Base64")
    except:
        basedata = "There was an error"
    
    return(basedata)
    
def hex_encode(encvalue):
    """ Encode value to Hex. Example Format: 48656c6c6f2576f726c64"""
    
    hexval = ""
    
    for item in encvalue:
        val = hex(ord(item)).strip("0x")
        hexval += val
        
    return(hexval)

def hexadecimal_escape(encvalue):
    """ Encode as hexadecimal escaped value: xss = \x78\x73\x73 """
    hexval = ""
    for item in encvalue:
        hexval += '\\x%02x' % (ord(item))
        
    return(hexval)

def octal_escape(encvalue):
    """ Encode as octal escaped value: xss = \x78\x73\x73 """
    octval = ""
    for item in encvalue:
        octval += '\\%03o' % (ord(item))
        
    return(octval)

def hex_entity_encode(encvalue):
    """ Encode value to a Hex entitiy. Example Format: &#x48;&#x65;&#x6c;&#x6c;&#x6f;"""
    
    hexval = ""
    
    for item in encvalue:
        val = hex(ord(item)).replace("0x", "&#x") + ";"
        hexval += val
        
    return(hexval)
    
def unicode_encode(encvalue):
    """ Unicode encode the specified value in the %u00 format. Example:
    %u0048%u0065%u006c%u006c%u006f%u0020%u0057%u006f%u0072%u006c%u0064 """
    
    hexval = ""
    
    for item in encvalue:
        val = hex(ord(item)).replace("0x", "%u00")
        hexval += val
        
    return(hexval)
    
def escape_xml(encvalue):
    """ Escape the specified HTML/XML value. Example Format: Hello&amp;World """
    
    escaped = escape(encvalue, {"'": "&apos;", '"': "&quot;"})
    
    return(escaped)
    
def md5_hash(encvalue):
    """ md5 hash the specified value.
    Example Format: b10a8db164e0754105b7a99be72e3fe5"""
    
    hashdata = hashlib.md5(encvalue).hexdigest()
    
    return(hashdata)
    
def sha1_hash(encvalue):
    """ sha1 hash the specified value.
    Example Format: 0a4d55a8d778e5022fab701977c5d840bbc486d0 """
    
    hashdata = hashlib.sha1(encvalue).hexdigest()
    
    return(hashdata)
    
def sqlchar_encode(encvalue):
    """ SQL char encode the specified value.
    Example Format: CHAR(72)+CHAR(101)+CHAR(108)+CHAR(108)+CHAR(111)"""
    
    charstring = ""
    
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
    
    for item in encvalue:
        val = "chr(" + str(ord(item)) + ")||"
        charstring += val
        
    return(charstring.rstrip("||"))

def decimal_convert(encvalue):
    """ Convert input to decimal value.
    Example Format: 721011081081113287111114108100 """
    
    decvalue = ""
    
    for item in encvalue:
        decvalue += str(ord(item))
    
    return(decvalue)

def decimal_entity_encode(encvalue):
    """ Convert input to a decimal entity.
    Example Format: &#72;&#101;&#108;&#108;&#111;&#32;&#87;&#111;&#114;&#108;&#100; """
    
    decvalue = ""
    
    for item in encvalue:
        decvalue += "&#" + str(ord(item)) +";"
        
    return(decvalue)

def rot13_encode(encvalue):
    """ Perform ROT13 encoding on the specified value.
    Example Format: Uryyb Jbeyq """
    
    return(encvalue.encode("rot13"))

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
    raw = encvalue.encode('utf-16be')
    for i in range(0, len(raw)/2):
        ch1, ch2 = raw[i*2], raw[i*2+1]
        if '\x00' == ch1 and '+' == ch2:
            result += '+-'
        elif '\x00' != ch1 or nonalphanum.match(ch2):
            bits = _int2bits(ord(ch1), 8) + _int2bits(ord(ch2), 8)
            bits += padbit * (6 - (len(bits)%6))
            result += '+'
            for offset in range(0, len(bits)/6):
                val = _bits2int(bits[offset*6:offset*6+6])
                result += alphabet[val]
            result += '-'
        else:
            result += ch2

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
    returnval = urllib.unquote(decvalue)
    
    return(returnval)
    
def fullurl_decode(decvalue):
    """ Full URL decode the specified value.
    Example Format: %48%65%6c%6c%6f%20%57%6f%72%6c%64 """
    
    splithex = decvalue.split("%")
    hexdec = ""
    for item in splithex:
        if item != "":
            hexdec += chr(int(item, 16))
            
    return(hexdec)
    
def base64_decode(decvalue):
    """ Base64 decode the specified value.
    Example Format: SGVsbG8gV29ybGQ= """
    
    msg = """ There was an error. Most likely this isn't a valid Base64 value
    and Python choked on it """
    
    try:
        base64dec = decvalue.decode("Base64")
        return(base64dec)
    except:
        return(msg)

def hex_decode(decvalue):
    """ Hex decode the specified value.
    Example Format: 48656c6c6f2576f726c64 """
    
    msg = """ There was an error, perhaps an invalid length for the hex
    value """
    
    try:
        decodeval = decvalue.decode("hex")
    except TypeError:
        # fallback, decode what is possible
        re_hex = re.compile(r'([0-9a-f]{2})', re.I)
        decodeval = re_hex.sub(lambda m: m.group(1).decode('hex'), decvalue)

    return(decodeval)

def hexadecimal_unescape(decvalue):
    """ Hex unescape the specified value.
    Example Format: \x48\x65\x6c\x6c\x6f\x25\x76\xf7\x26\xc64 """

    re_hex = re.compile(r'\\x([0-9a-f]{2})', re.I)
    decodeval = re_hex.sub(lambda m: m.group(1).decode('hex'), decvalue)
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
    
    charval = ""
    splithex = decvalue.split("%u00")
    
    for item in splithex:
        if item != "":
            hexcon = item.replace("%u00", "0")
            charcon = chr(int(hexcon, 16))
            charval += charcon
        else:
            pass
        
    return(charval)
    
def rot13_decode(decvalue):
    """ ROT13 decode the specified value. Example Format: Uryyb Jbeyq  """
    
    return(decvalue.decode("rot13"))

def utf7_decode(decvalue):
    """ UTF-7 decode value including values with bad padding """
    result = ''
    i = 0
    valuelen = len(decvalue)
    while i < valuelen:
        ch = decvalue[i]
        i += 1
        if '+' == ch:
            if '-' == decvalue[i]:
                result += '+'
            else:
                tmp = ''
                while '-' != decvalue[i]:
                    tmp += decvalue[i]
                    i += 1
                tmp += '=' * (4 - (len(tmp)%4))
                val = tmp.decode('base64')
                for j in range(0, len(val)/2):
                    result += val[j*2:j*2+2].decode('utf-16be')
            i += 1
        else:
            result += ch

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
        print('unimplemented decode method,', decode_method)

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
