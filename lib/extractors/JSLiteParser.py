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

import re

class JSLiteParser():

    S_BEGIN = 0
    S_QUOTE = 1
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
        self.re_identifier = re.compile(r'^[$_a-zA-Z0-9.]+$')
        self.re_keywords = re.compile(r'^(?:break|case|catch|const|continue|debugger|default|delete|do|else|enum|false|finally|for|function|if|in|instanceof|new|null|return|switch|this|throw|true|try|typeof|var|void|while|with)$')
        self.re_no_regex_start = re.compile(r'[\]]')
        self.re_space = re.compile(r'\s')

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
        escape_next = False
        qchar = ''
        last_token = ''
        regex_paren_level = 0
        regex_use_heuristic = False
        pos = 0
        start_pos = pos
        s_len = len(script)
        rewind_pos = 0
        last_was_identifier = False
        while pos < s_len:
            c = script[pos]
            try:
                if escape_next:
                    escape_next = False
                elif self.S_COMMENT == state:
                    if '*' == c:
                        state = self.S_STAR
                    else:
                        pass
                elif self.S_STAR == state:
                    if '/' == c:
                        self._comments.append(script[start_pos:pos+1])
                        state = self.S_BEGIN
                        start_pos = pos
                    elif '*' == c:
                        pass
                    else:
                        state = self.S_COMMENT
                elif '\n' == c:
                    # newlines break everything except multiline-comment
                    if self.S_LINE_COMMENT == state:
                        self._comments.append(script[start_pos:pos])
                    elif state in (self.S_REGEXP, self.S_REGEXP_CC):
                        # invalid regex
                        pos = rewind_pos
                    if state != self.S_COMMENT:
                        state = self.S_BEGIN
                        start_pos = pos
                        last_token = None
                elif self.S_QUOTE == state:
                    if '\\' == c:
                        escape_next = True
                    elif qchar == c:
                        self._strings.append(self.parseString(script[start_pos+1:pos]))
                        state = self.S_BEGIN
                        start_pos = pos
                    else:
                        pass
                elif self.S_REGEXP == state:
                    if '\\' == c:
                        escape_next = True
                    elif '[' == c:
                        state = self.S_REGEXP_CC
                    elif ')' == c and 0 == regex_paren_level:
                        # not valid
                        pos = rewind_pos
                        state = self.S_BEGIN
                        start_pos = pos
                    elif ';' == c and regex_use_heuristic and self.re_identifier.match(script[start_pos:pos].rstrip()):
                        # probably not valid
                        pos = rewind_pos
                        state = self.S_BEGIN
                        start_pos = pos
                    elif '/' == c:
#                        print('regex=',script[start_pos:pos])
                        state = self.S_BEGIN
                        start_pos = pos
                    else:
                        if '(' == c:
                            regex_paren_level += 1
                        elif ')' == c:
                            regex_paren_level -= 1
                elif self.S_REGEXP_CC == state:
                    if '\\' == c:
                        escape_next = True
                    elif ']' == c:
                        state = self.S_REGEXP
                    else:
                        pass
                elif self.S_LINE_COMMENT == state:
                    pass
                elif self.S_SLASH == state:
                    if '*' == c:
                        state = self.S_COMMENT
                    elif '/' == c:
                        state = self.S_LINE_COMMENT
                        last_token = None
                    else:
                        if last_token:
                            if self.re_identifier.match(last_token) and not self.re_keywords.match(last_token):
                                is_re = False
                            elif self.re_no_regex_start.match(last_token):
                                is_re = False
                            else:
                                is_re = True
                        else:
                            is_re = True
                        if is_re:
                            if ')' == last_token:
                                regex_use_heuristic = True
                            else:
                                regex_use_heuristic = False
                            regex_paren_level = 0
                            rewind_pos = pos
                            if '[' == c:
                                state = self.S_REGEXP_CC
                            else:
                                state = self.S_REGEXP
                                if '\\' == c:
                                    escape_next = True
                                elif '(' == c:
                                    regex_paren_level += 1
                            start_pos = pos
                        else:
                            state = self.S_BEGIN
                elif self.S_BEGIN == state:
                    if ';' == c:
                        last_token = None
                        start_pos = pos
                        last_was_identifier = False
                    elif '"' == c:
                        state = self.S_QUOTE
                        qchar = c
                        start_pos = pos
                        last_token = '__string__'
                        last_was_identifier = False
                    elif "'" == c:
                        state = self.S_QUOTE
                        qchar = c
                        start_pos = pos
                        last_token = '__string__'
                        last_was_identifier = False
                    elif '/' == c:
                        state = self.S_SLASH
                        this_token = script[start_pos:pos]
                        if this_token:
                            last_token = this_token
                        start_pos = pos
                        last_was_identifier = False
                    elif self.re_identifier.match(c):
                        if not last_was_identifier:
                            this_token = script[start_pos:pos]
                            if this_token:
                                last_token = this_token
                                start_pos = pos
                        last_was_identifier = True
                    else:
                        this_token = script[start_pos:pos]
                        if this_token:
                            last_token = this_token
                            start_pos = pos
                        last_was_identifier = False
                else:
                    raise Exception('unhandled state=' + state)

            except UnicodeEncodeError:
                # TODO: do something with char
                pass
            pos += 1

if '__main__' == __name__:
    import sys
    parser = JSLiteParser()
    for a in sys.argv[1:]:
        script=open(a).read()
        parser.parse(script)
        print('\n'.join([s.encode('ascii', 'ignore') for s in parser.strings()]))
        print(parser.comments())


