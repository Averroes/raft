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

from cStringIO import StringIO
import re

class JSLiteParser():

    S_BEGIN = 0
    S_D_QUOTE = 1
    S_S_QUOTE = 2
    S_REGEXP = 3
    S_COMMENT = 4
    S_LINE_COMMENT = 5
    S_SLASH = 6
    S_STAR = 7
    S_REGEXP_CC = 8

    def __init__(self):
        self._strings = []
        self._comments = []
        self.re_octal_digits = re.compile('[0-7]{3}')
        self.re_escape_string = re.compile(r'\\(?:[0-7]{3}|x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|.)')
        self.re_non_word = re.compile(r'\W')
        self.re_fp = re.compile(r'^\d+\.\d*(?:[eE][-+]?\d+)?|^\d+(?:\.\d*)?[eE][-+]?\d+|^\.\d+(?:[eE][-+]?\d+)?')
        self.re_integer = re.compile(r'^0[xX][\da-fA-F]+|^0[0-7]*|^\d+')

    def reset(self):
        self._strings = []
        self._comments = []

    def strings(self):
        return self._strings

    def comments(self):
        return self._comments

    def parse(self, script, filename = '', lineno = 0):
        self.process(script)

    def parse_file(self, script, filename = '', lineno = 0):
        self.reset()
        self.process(script)

    def interpretEscape(self, match):
        m = match.group(0)[1:]
        if '0' == m:
            return '\0'
        elif 'b' == m:
            return '\b'
        elif 'f' == m:
            return '\f'
        elif 'n' == m:
            return '\n'
        elif 'r' == m:
            return '\r'
        elif 't' == m:
            return '\t'
        elif 'v' == m:
            return '\v'
        elif '\'' == m:
            return '\''
        elif '"' == m:
            return '"'
        elif '\\' == m:
            return '\\'
        else:
            try:
                i = None
                if 'u' == m[0] and 5 == len(m):
                    i = int(m[1:], 16)
                elif 'x' == m[0] and 3 == len(m):
                    i = int(m[1:], 16)
                elif 3 == len(m) and self.re_octal_digits.match(m):
                    i = int(m, 8)
                if i is not None:
                    if i < 128:
                        return chr(i)
                    else:
                        return unichr(i)
                else:
                    return m
            except ValueError:
                return m

    def parseString(self, value):
        if '\\' in value:
            try:
                return self.re_escape_string.sub(self.interpretEscape, value)
            except UnicodeDecodeError:
                print('oops', value)
        return value

    def process(self, script):
        state = self.S_BEGIN
        current_io = StringIO()
        escape_next = False
        last_token = ''
        for c in script:
            try:
                if escape_next:
                    current_io.write(c)
                    escape_next = False
                elif self.S_COMMENT == state:
                    if '*' == c:
                        state = self.S_STAR
                    else:
                        current_io.write(c)
                elif self.S_STAR == state:
                    if '/' == c:
                        self._comments.append(current_io.getvalue())
                        state = self.S_BEGIN
                        current_io = StringIO()
                    else:
                        current_io.write('*')
                        current_io.write(c)
                        state = self.S_COMMENT
                elif '\n' == c:
                    # newlines break everything escape multiline-comment
                    if self.S_LINE_COMMENT == state:
                        self._comments.append(current_io.getvalue())
                    state = self.S_BEGIN
                    current_io = StringIO()
                elif self.S_D_QUOTE == state:
                    if '\\' == c:
                        current_io.write(c)
                        escape_next = True
                    elif '"' == c:
                        self._strings.append(self.parseString(current_io.getvalue()))
                        state = self.S_BEGIN
                        current_io = StringIO()
                    else:
                        current_io.write(c)
                elif self.S_S_QUOTE == state:
                    if '\\' == c:
                        current_io.write(c)
                        escape_next = True
                    elif "'" == c:
                        self._strings.append(self.parseString(current_io.getvalue()))
                        state = self.S_BEGIN
                        current_io = StringIO()
                    else:
                        current_io.write(c)
                elif self.S_REGEXP == state:
                    if '\\' == c:
                        current_io.write(c)
                        escape_next = True
                    elif '[' == c:
                        current_io.write(c)
                        state = self.S_REGEXP_CC
                    elif '/' == c:
    #                    print('regex=',current_io.getvalue())
                        state = self.S_BEGIN
                        current_io = StringIO()
                    else:
                        current_io.write(c)
                elif self.S_REGEXP_CC == state:
                    if '\\' == c:
                        current_io.write(c)
                        escape_next = True
                    elif ']' == c:
                        current_io.write(c)
                        state = self.S_REGEXP
                    else:
                        current_io.write(c)
                elif self.S_LINE_COMMENT == state:
                    current_io.write(c)
                elif self.S_SLASH == state:
                    if '*' == c:
                        state = self.S_COMMENT
                        current_io = StringIO()
                    elif '/' == c:
                        state = self.S_LINE_COMMENT
                        current_io = StringIO()
                    elif last_token:
    #                    print('checking token:' + last_token)
                        if self.re_fp.match(last_token) or self.re_integer.match(last_token):
                            pass
                        else:
                            if '[' == c:
                                state = self.S_REGEXP_CC
                            else:
                                state = self.S_REGEXP
                            current_io = StringIO()
                            current_io.write(c)
                elif self.S_BEGIN == state:
                    if self.re_non_word.match(c):
                        this_token = current_io.getvalue()
                        if this_token:
    #                        print('--->', this_token)
                            last_token = this_token
                            current_io = StringIO()
                    else:
                        current_io.write(c)

                    if '"' == c:
                        state = self.S_D_QUOTE
                        current_io = StringIO()
                    elif "'" == c:
                        state = self.S_S_QUOTE
                        current_io = StringIO()
                    elif '/' == c:
                        state = self.S_SLASH
            except UnicodeEncodeError:
                # TODO: do something with char
                pass

if '__main__' == __name__:
    import sys
    parser = JSLiteParser()
    for a in sys.argv[1:]:
        script=open(a).read()
        parser.parse(script)
        print('\n'.join([s.encode('ascii', 'ignore') for s in parser.strings()]))
#        print(parser.comments())

