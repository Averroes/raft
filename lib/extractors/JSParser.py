#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2011 RAFT Team
#
# This file is part of RAFT.
#
#
# The Original Code is the Narcissus JavaScript engine.
#
# The Initial Developer of the Original Code is
# Brendan Eich <brendan@mozilla.org>.
# Portions created by the Initial Developer are Copyright (C) 2004
# the Initial Developer. All Rights Reserved.
#
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


################################################################
#
# the following is generated from JSDef.py 
# it must be rengerated and copied here if the JS grammar changes
#
################################################################
T_END = 0
T_NEWLINE = 1
T_SEMICOLON = 2
T_COMMA = 3
T_ASSIGN = 4
T_HOOK = 5
T_COLON = 6
T_CONDITIONAL = 7
T_OR = 8
T_AND = 9
T_BITWISE_OR = 10
T_BITWISE_XOR = 11
T_BITWISE_AND = 12
T_EQ = 13
T_NE = 14
T_STRICT_EQ = 15
T_STRICT_NE = 16
T_LT = 17
T_LE = 18
T_GE = 19
T_GT = 20
T_LSH = 21
T_RSH = 22
T_URSH = 23
T_PLUS = 24
T_MINUS = 25
T_MUL = 26
T_DIV = 27
T_MOD = 28
T_NOT = 29
T_BITWISE_NOT = 30
T_UNARY_PLUS = 31
T_UNARY_MINUS = 32
T_INCREMENT = 33
T_DECREMENT = 34
T_DOT = 35
T_LEFT_BRACKET = 36
T_RIGHT_BRACKET = 37
T_LEFT_CURLY = 38
T_RIGHT_CURLY = 39
T_LEFT_PAREN = 40
T_RIGHT_PAREN = 41
T_SCRIPT = 42
T_BLOCK = 43
T_LABEL = 44
T_FOR_IN = 45
T_CALL = 46
T_NEW_WITH_ARGS = 47
T_INDEX = 48
T_ARRAY_INIT = 49
T_OBJECT_INIT = 50
T_PROPERTY_INIT = 51
T_GETTER = 52
T_SETTER = 53
T_GROUP = 54
T_LIST = 55
T_IDENTIFIER = 56
T_NUMBER = 57
T_STRING = 58
T_REGEXP = 59
T_BREAK = 60
T_CASE = 61
T_CATCH = 62
T_CONST = 63
T_CONTINUE = 64
T_DEBUGGER = 65
T_DEFAULT = 66
T_DELETE = 67
T_DO = 68
T_ELSE = 69
T_ENUM = 70
T_FALSE = 71
T_FINALLY = 72
T_FOR = 73
T_FUNCTION = 74
T_IF = 75
T_IN = 76
T_INSTANCEOF = 77
T_NEW = 78
T_NULL = 79
T_RETURN = 80
T_SWITCH = 81
T_THIS = 82
T_THROW = 83
T_TRUE = 84
T_TRY = 85
T_TYPEOF = 86
T_VAR = 87
T_VOID = 88
T_WHILE = 89
T_WITH = 90

TOKENS = {0: 'END', 1: '\n', 2: ';', 3: ',', 4: '=', 5: '?', 6: ':', 7: 'CONDITIONAL', 8: '||', 9: '&&', '||': 8, 11: '^', 12: '&', 13: '==', 14: '!=', 15: '===', 16: '!==', 17: '<', 18: '<=', 19: '>=', 20: '>', 21: '<<', 22: '>>', 23: '>>>', 24: '+', 25: '-', 26: '*', 27: '/', 28: '%', 29: '!', 30: '~', 31: 'UNARY_PLUS', 32: 'UNARY_MINUS', 33: '++', 34: '--', 35: '.', 36: '[', 37: ']', 38: '{', 39: '}', 40: '(', 41: ')', 42: 'SCRIPT', 43: 'BLOCK', 44: 'LABEL', ',': 3, 46: 'CALL', 47: 'NEW_WITH_ARGS', 48: 'INDEX', '>>>': 23, 50: 'OBJECT_INIT', 51: 'PROPERTY_INIT', 52: 'GETTER', 53: 'SETTER', 54: 'GROUP', 55: 'LIST', 56: 'IDENTIFIER', 57: 'NUMBER', 58: 'STRING', 59: 'REGEXP', 60: 'break', 10: '|', 62: 'catch', 63: 'const', 64: 'continue', 'case': 61, 66: 'default', 67: 'delete', 68: 'do', 69: 'else', 70: 'enum', 71: 'false', '==': 13, 73: 'for', 74: 'function', 75: 'if', 76: 'in', 77: 'instanceof', 78: 'new', 79: 'null', 'break': 60, 81: 'switch', 82: 'this', 83: 'throw', 84: 'true', 85: 'try', 86: 'typeof', 87: 'var', 88: 'void', 89: 'while', 90: 'with', 'UNARY_PLUS': 31, 'ARRAY_INIT': 49, 'instanceof': 77, '--': 34, 'try': 85, 'this': 82, 'UNARY_MINUS': 32, '|': 10, 'INDEX': 48, 'GROUP': 54, 'NEW_WITH_ARGS': 47, 'LABEL': 44, 'BLOCK': 43, 'SETTER': 53, 'const': 63, 'for': 73, '+': 24, '/': 27, 'continue': 64, 'new': 78, ';': 2, '?': 5, 'END': 0, 'do': 68, 'enum': 70, 'GETTER': 52, '&&': 9, 'REGEXP': 59, '[': 36, 'throw': 83, '!==': 16, '++': 33, 'SCRIPT': 42, '(': 40, '{': 38, 'delete': 67, 'CONDITIONAL': 7, '>=': 19, '>>': 22, '\n': 1, 45: 'FOR_IN', '!=': 14, 'finally': 72, 'debugger': 65, '&': 12, '*': 26, 61: 'case', '.': 35, 'var': 87, 'STRING': 58, ':': 6, '>': 20, 'function': 74, 'with': 90, 'else': 69, 'catch': 62, 'true': 84, '^': 11, '===': 15, 'IDENTIFIER': 56, 'default': 66, 'LIST': 55, '<': 17, 'while': 89, 'typeof': 86, '~': 30, 'false': 71, 65: 'debugger', '<<': 21, '<=': 18, 'NUMBER': 57, 'in': 76, 'return': 80, 'null': 79, 'if': 75, '!': 29, 'FOR_IN': 45, '%': 28, ')': 41, '-': 25, 72: 'finally', '=': 4, 'void': 88, 49: 'ARRAY_INIT', ']': 37, 80: 'return', 'PROPERTY_INIT': 51, 'switch': 81, 'CALL': 46, 'OBJECT_INIT': 50, '}': 39}

OP_TYPE_NAMES = {'>=': 'GE', '>>': 'RSH', '<<': 'LSH', '<=': 'LE', '!=': 'NE', '!': 'NOT', '%': 'MOD', '&': 'BITWISE_AND', ')': 'RIGHT_PAREN', '(': 'LEFT_PAREN', '+': 'PLUS', '*': 'MUL', '-': 'MINUS', ',': 'COMMA', '/': 'DIV', '.': 'DOT', '>>>': 'URSH', ';': 'SEMICOLON', ':': 'COLON', '=': 'ASSIGN', '||': 'OR', '?': 'HOOK', '>': 'GT', '\n': 'NEWLINE', '==': 'EQ', '&&': 'AND', '[': 'LEFT_BRACKET', ']': 'RIGHT_BRACKET', '^': 'BITWISE_XOR', '===': 'STRICT_EQ', '!==': 'STRICT_NE', '++': 'INCREMENT', '<': 'LT', '--': 'DECREMENT', '{': 'LEFT_CURLY', '}': 'RIGHT_CURLY', '|': 'BITWISE_OR', '~': 'BITWISE_NOT'}

OP_REGEX = '^\\;|^\\,|^\\?|^\\:|^\\|\\||^\\&\\&|^\\||^\\^|^\\&|^\\=\\=\\=|^\\=\\=|^\\=|^\\!\\=\\=|^\\!\\=|^\\<\\<|^\\<\\=|^\\<|^\\>\\>\\>|^\\>\\>|^\\>\\=|^\\>|^\\+\\+|^\\-\\-|^\\+|^\\-|^\\*|^\\/|^\\%|^\\!|^\\~|^\\.|^\\[|^\\]|^\\{|^\\}|^\\(|^\\)'

KEYWORDS = {'false': 71, 'debugger': 65, 'in': 76, 'null': 79, 'if': 75, 'const': 63, 'for': 73, 'with': 90, 'while': 89, 'finally': 72, 'var': 87, 'new': 78, 'function': 74, 'do': 68, 'return': 80, 'void': 88, 'enum': 70, 'else': 69, 'break': 60, 'catch': 62, 'instanceof': 77, 'true': 84, 'throw': 83, 'case': 61, 'default': 66, 'try': 85, 'this': 82, 'switch': 81, 'continue': 64, 'typeof': 86, 'delete': 67}

ASSIGN_OPS = {'%': 28, '>>': 22, '&': 12, '<<': 21, '*': 26, '-': 25, '/': 27, '>>>': 23, '+': 24, '|': 10, '^': 11}

GLOBAL = {'VOID': 88, 'RIGHT_BRACKET': 37, 'UNARY_MINUS': 32, 'RIGHT_PAREN': 41, 'STRICT_EQ': 15, 'TRUE': 84, 'MINUS': 25, 'NEWLINE': 1, 'PLUS': 24, 'GT': 20, 'DEBUGGER': 65, 'ENUM': 70, 'GE': 19, 'VAR': 87, 'ARRAY_INIT': 49, 'BITWISE_XOR': 11, 'RETURN': 80, 'BITWISE_NOT': 30, 'THIS': 82, 'TYPEOF': 86, 'OR': 8, 'DELETE': 67, 'INDEX': 48, 'GROUP': 54, 'NEW_WITH_ARGS': 47, 'LABEL': 44, 'BITWISE_AND': 12, 'NEW': 78, 'BLOCK': 43, 'SETTER': 53, 'WITH': 90, 'LSH': 21, 'COLON': 6, 'UNARY_PLUS': 31, 'FUNCTION': 74, 'END': 0, 'FOR': 73, 'ELSE': 69, 'TRY': 85, 'GETTER': 52, 'REGEXP': 59, 'EQ': 13, 'DECREMENT': 34, 'AND': 9, 'CONTINUE': 64, 'NOT': 29, 'LEFT_CURLY': 38, 'RIGHT_CURLY': 39, 'DEFAULT': 66, 'STRICT_NE': 16, 'WHILE': 89, 'MUL': 26, 'DOT': 35, 'CASE': 61, 'SEMICOLON': 2, 'SCRIPT': 42, 'CONDITIONAL': 7, 'LEFT_PAREN': 40, 'NE': 14, 'SWITCH': 81, 'INCREMENT': 33, 'CATCH': 62, 'IDENTIFIER': 56, 'INSTANCEOF': 77, 'FALSE': 71, 'LIST': 55, 'BREAK': 60, 'BITWISE_OR': 10, 'LEFT_BRACKET': 36, 'DO': 68, 'CONST': 63, 'NUMBER': 57, 'HOOK': 5, 'DIV': 27, 'NULL': 79, 'LE': 18, 'URSH': 23, 'LT': 17, 'COMMA': 3, 'ASSIGN': 4, 'STRING': 58, 'FINALLY': 72, 'FOR_IN': 45, 'IN': 76, 'IF': 75, 'RSH': 22, 'PROPERTY_INIT': 51, 'CALL': 46, 'OBJECT_INIT': 50, 'MOD': 28, 'THROW': 83}

OP_PRECEDENCE = {2: 0, 3: 1, 4: 2, 5: 2, 6: 2, 8: 4, 9: 5, 10: 6, 11: 7, 12: 8, 13: 9, 14: 9, 15: 9, 16: 9, 17: 10, 18: 10, 19: 10, 20: 10, 21: 11, 22: 11, 23: 11, 24: 12, 25: 12, 26: 13, 27: 13, 28: 13, 29: 14, 30: 14, 31: 14, 32: 14, 33: 15, 34: 15, 35: 17, 67: 14, 76: 10, 77: 10, 78: 16, 86: 14, 88: 14}

OP_ARITY = {3: -2, 4: 2, 5: 3, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2, 13: 2, 14: 2, 15: 2, 16: 2, 17: 2, 18: 2, 19: 2, 20: 2, 21: 2, 22: 2, 23: 2, 24: 2, 25: 2, 26: 2, 27: 2, 28: 2, 29: 1, 30: 1, 31: 1, 32: 1, 33: 1, 34: 1, 35: 2, 46: 2, 47: 2, 48: 2, 49: 1, 50: 1, 54: 1, 67: 1, 76: 2, 77: 2, 78: 1, 86: 1, 88: 1}
################################################################

T_DECLARED_FORM = 0
T_EXPRESSED_FORM = 1
T_STATEMENT_FORM = 2

class JsParseException(Exception):
    def __init__(self, msg, *args):
        Exception.__init__(self, msg, args)

class Token():
    def __init__(self):
        self.ttype = 0
        self.value = ''
        self.assignOp = 0
        self.start = 0
        self.end = 0
        self.lineno = 0

class Tokenizer():
    def __init__(self):
        self.re_lead_space_or_tab = re.compile(r'^[ \t]+')
        self.re_leading_spaces = re.compile(r'^\s+')
        self.re_comment = re.compile(r'^\/(?:\*(?:.|\n)*?\*\/|\/.*)')
        self.re_op = re.compile(OP_REGEX)
        self.re_fp = re.compile(r'^\d+\.\d*(?:[eE][-+]?\d+)?|^\d+(?:\.\d*)?[eE][-+]?\d+|^\.\d+(?:[eE][-+]?\d+)?')
        self.re_re = re.compile(r'^\/((?:\\.|\[(?:\\.|[^\]])*\]|[^\/])+)\/([gimy]*)')
        self.re_integer = re.compile(r'^0[xX][\da-fA-F]+|^0[0-7]*|^\d+')
        self.re_identifier = re.compile(r'^[$_\w]+')
        self.re_string = re.compile(r'^"(?:\\.|[^"])*"|^\'(?:\\.|[^\'])*\'')
        self.re_newline = re.compile(r'^\n')
        self.re_octal_digits = re.compile('[0-7]{3}')
        self.re_escape_string = re.compile(r'\\(?:[0-7]{3}|x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|.)')

        # collect these directly for simplicity
        self.comments = []
        self.strings = []

    def reset(self, source, filename = '', lineno = 0, reset_collections = False):
        self.cursor = 0
        self.source = source
        self.tokens = [None for m in range(4)]
        self.tokenIndex = 0
        self.lookahead = 0
        self.scanNewlines = False
        self.scanOperand = True
        self.filename = filename
        self.lineno = lineno
        if reset_collections:
            self.comments = []
            self.strings = []
        
    def script_input(self):
        return self.source[self.cursor:]

    def done(self):
        return self.peek() == T_END

    def token(self):
        if self.tokenIndex >= len(self.tokens):
            return None
        return self.tokens[self.tokenIndex]

    def match(self, tt):
        return (self.get() == tt) or self.unget()

    def mustMatch(self, tt):
        if not self.match(tt):
            raise self.newSyntaxError('Missing ' + TOKENS[tt].lower())
        return self.token()

    def peek(self):
        if self.lookahead > 0:
            next = self.tokens[(self.tokenIndex + self.lookahead) & 3]
            if self.scanNewlines and next.lineno != self.lineno:
                tt = T_NEWLINE
            else:
                tt = next.ttype
        else:
            tt = self.get()
            self.unget()
        return tt

    def peekOnSameLine(self):
        self.scanNewlines = True
        tt = self.peek()
        self.scanNewlines = False
        return tt

    def get(self):
        token = None
        while self.lookahead > 0:
            self.lookahead -= 1
            self.tokenIndex = (self.tokenIndex + 1) & 3
            token = self.tokens[self.tokenIndex]
            if token.ttype != T_NEWLINE or self.scanNewlines:
                return token.ttype
        while True:
            script_input = self.script_input()
            if self.scanNewlines:
                match = self.re_lead_space_or_tab.match(script_input)
            else:
                match = self.re_leading_spaces.match(script_input)
            if match:
                spaces = match.group(0)
                self.cursor += len(spaces)
                self.lineno += spaces.count('\n')
                script_input = self.script_input()

            match = self.re_comment.match(script_input)
            if not match:
                break
            comment = match.group(0)
            self.comments.append(comment)
            self.cursor += len(comment)
            self.lineno += comment.count('\n')

        self.tokenIndex = (self.tokenIndex + 1) & 3
        token = self.tokens[self.tokenIndex]
        if not token:
            self.tokens[self.tokenIndex] = token = Token()

        if not script_input:
            token.ttype = T_END
            return token.ttype

        matched = ''
        match = None
        while True:
            match = self.re_fp.match(script_input)
            if match:
                token.ttype = T_NUMBER
                token.value = self.parseFloat(match.group(0))
                break
            match = self.re_integer.match(script_input)
            if match:
                token.ttype = T_NUMBER
                token.value = self.parseInt(match.group(0))
                break
            match = self.re_identifier.match(script_input)
            if match:
                Id = match.group(0)
                if KEYWORDS.has_key(Id):
                    token.ttype = KEYWORDS[Id]
                else:
                    token.ttype = T_IDENTIFIER
                token.value = Id
                break
            match = self.re_string.match(script_input)
            if match:
                token.ttype = T_STRING
                string = self.parseString(match.group(0))
                self.strings.append(string)
                token.value = string
                break
            if self.scanOperand:
                match = self.re_re.match(script_input)
                if match:
                    token.ttype = T_REGEXP
                    token.value = self.parseRegexp(match.group(1), match.group(2))
                    break
            match = self.re_op.match(script_input)
            if match:
                op = match.group(0)
                if ASSIGN_OPS.has_key(op) and script_input[len(op)] == '=':
                    token.ttype = T_ASSIGN
                    token.assignOp = GLOBAL[OP_TYPE_NAMES[op]]
                    matched = match.group(0) + '='
                else:
                    token.ttype = GLOBAL[OP_TYPE_NAMES[op]]
                    if self.scanOperand and token.ttype in (T_PLUS, T_MINUS):
                        token.ttype += T_UNARY_PLUS - T_PLUS
                    token.assignOp = None
                token.value = op
                break
            match = self.re_newline.match(script_input)
            if self.scanNewlines and match:
                token.ttype = T_NEWLINE
                break

            raise self.newSyntaxError('Illegal token: [%s]' % repr(script_input[0:48]))

####        print('token', token.ttype, token.value)
        token.start = self.cursor
        if not matched:
            matched = match.group(0)
        self.cursor += len(matched)
        token.end = self.cursor
        token.lineno = self.lineno
        return token.ttype

    def unget(self):
        self.lookahead += 1
        if self.lookahead >= 4:
            raise Exception('PANIC: too much lookahead')
        self.tokenIndex = (self.tokenIndex - 1 ) & 3

    def newSyntaxError(self, msg):
        err = '%s: %s, %s' % (msg, self.filename, self.lineno)
        return JsParseException(err)

    # TODO: implement these
    def parseFloat(self, value):
        return value

    def parseInt(self, value):
        return value

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
                return self.re_escape_string.sub(self.interpretEscape, value[1:-1])
            except UnicodeDecodeError:
                print('oops', value)
        return value[1:-1]

    def parseRegexp(self, value, flags):
        return value + ',' + flags

class CompilerContext:
    def __init__(self, inFunction):
        self.inFunction = inFunction
        self.stmtStack = []
        self.funDecls = []
        self.varDecls = []

        self.bracketLevel = self.curlyLevel = self.parenLevel = self.hookLevel = 0
        self.ecmaStrictMode = self.inForLoopInit = False

def Script(t, x):
    n = Statements(t, x)
    n.ttype = T_SCRIPT
    n.funDecls = x.funDecls
    n.varDecls = x.varDecls
    return n

class Node(list):
    def __init__(self, tokenizer, ttype = None, *args):
        list.__init__(self)
        token = tokenizer.token()
        self.indentLevel = 0
        if token:
            self.ttype = ttype or token.ttype
            self.value = token.value
            self.lineno = token.lineno
            self.start = token.start
            self.end = token.end
        else:
            self.ttype = ttype
            self.value = ''
            self.lineno = tokenizer.lineno
            self.start = 0
            self.end = 0

#        self.tokenizer = tokenizer
        self.label = None
        self.isLoop = False

        for arg in args:
            self.append(arg)

    def append(self, kid):
        if kid is not None:
            if kid.start < self.start:
                self.start = kid.start
            if self.end < kid.end:
                self.end = kid.end
        return list.append(self, kid)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        INDENTATION = "    ";
        n = self.indentLevel + 1;
        s = "{\n" + (INDENTATION *n) + "type: " + tokenstr(self.ttype);
        for name in dir(self):
            if name[0] != '_' and not hasattr(list, name):
                s += ",\n" + (INDENTATION*n) + ('%s: %s' % (name, getattr(self,name)))
        n = self.indentLevel - 1;
        s += "\n" + (INDENTATION * n) + "}";
        return s;

#    def getSource(self):
#        return self.tokenizer.source[self.start:self.end]

#    def filename(self):
#        return self.tokenizer.filename

def tokenstr(tt):
    t = TOKENS.get(tt)
    if OP_TYPE_NAMES.has_key(t):
        return OP_TYPE_NAMES[t]
    else:
        return str(t).upper()

def nest(t, x, node, func, end = None):
    x.stmtStack.append(node)
    n = func(t, x)
    x.stmtStack.pop()
    if end:
        t.mustMatch(end)
    return n

def Statements(t, x):
    n = Node(t, T_BLOCK)
    x.stmtStack.append(n)
    while ( not t.done() and t.peek() != T_RIGHT_CURLY):
        n.append(Statement(t, x))
    x.stmtStack.pop()
    return n

def Block(t, x):
    t.mustMatch(T_LEFT_CURLY)
    n = Statements(t, x)
    t.mustMatch(T_RIGHT_CURLY)
    return n

def Statement(t, x) :
    i, label, n, n2, ss = None, None, None, None, None

    tt = t.get()

####    print('Statement', tt)

    if T_FUNCTION == tt:
        if len(x.stmtStack) > 1:
            return FunctionDefinition(t, x, True, T_STATEMENT_FORM)
        else:
            return FunctionDefinition(t, x, True, T_DECLARED_FORM)

    elif T_LEFT_CURLY == tt:
        n = Statements(t, x)
        t.mustMatch(T_RIGHT_CURLY)
        return n

    elif T_IF == tt:
        n = Node(t)
        n.condition = ParenExpression(t, x)
        x.stmtStack.append(n)
        n.thenPart = Statement(t, x)
        if t.match(T_ELSE):
            n.elsePart = Statement(t, x)
        else:
            n.elsePart = None
        x.stmtStack.pop()
        return n
    
    elif T_SWITCH == tt:
        n = Node(t)
        t.mustMatch(T_LEFT_PAREN)
        n.discriminant = Expression(t, x)
        t.mustMatch(T_RIGHT_PAREN)
        n.cases = []
        n.defaultIndex = -1
        x.stmtStack.append(n)
        t.mustMatch(T_LEFT_CURLY)
        while True:
            tt = t.get()
            if tt == T_RIGHT_CURLY:
                break
            if tt in (T_DEFAULT, T_CASE):
                if T_DEFAULT == tt:
                    if (n.defaultIndex >= 0):
                        raise t.newSyntaxError("More than one switch default")
                n2 = Node(t)
                if (tt == T_DEFAULT):
                    n.defaultIndex = len(n.cases)
                else:
                    n2.caseLabel = Expression(t, x, T_COLON)
            else:
                raise t.newSyntaxError("Invalid switch case")
            t.mustMatch(T_COLON)
            n2.statements = Node(t, T_BLOCK)
            while True:
                tt=t.peek()
                if tt in (T_CASE, T_DEFAULT, T_RIGHT_CURLY):
                    break
                n2.statements.append(Statement(t, x))
            n.cases.append(n2)
        x.stmtStack.pop()
        return n

    elif T_FOR == tt:
        n = Node(t)
        n.isLoop = True
        t.mustMatch(T_LEFT_PAREN)
        tt = t.peek()
        if (tt != T_SEMICOLON):
            x.inForLoopInit = True
            if (tt == T_VAR or tt == T_CONST):
                t.get()
                n2 = Variables(t, x)
            else:
                n2 = Expression(t, x)
            x.inForLoopInit = False
        if n2 is not None and t.match(T_IN):
            n.ttype = T_FOR_IN
            if (n2.ttype == T_VAR):
                if (len(n2) != 1):
                    raise Exception("Invalid for..in left-hand side" % (t.filename, n2.lineno))
                n.iterator = n2[0]
                n.varDecl = n2
            else:
                n.iterator = n2
                n.varDecl = None
            n.object = Expression(t, x)
        else:
            n.setup = n2 or None
            t.mustMatch(T_SEMICOLON)
            if (t.peek() == T_SEMICOLON):
                n.condition = None
            else:
                n.condition = Expression(t, x)
            t.mustMatch(T_SEMICOLON)
            if (t.peek() == T_RIGHT_PAREN):
                n.update = None
            else:
                n.update =  Expression(t, x)
        t.mustMatch(T_RIGHT_PAREN)
        n.body = nest(t, x, n, Statement)
        return n

    elif T_WHILE == tt:
        n = Node(t)
        n.isLoop = True
        n.condition = ParenExpression(t, x)
        n.body = nest(t, x, n, Statement)
        return n

    elif T_DO == tt:
        n = Node(t)
        n.isLoop = True
        n.body = nest(t, x, n, Statement, T_WHILE)
        n.condition = ParenExpression(t, x)
        if not x.ecmaStrictMode:
            # // <script language="JavaScript"> (without version hints) may need
            # // automatic semicolon insertion without a newline after do-while.
            # // See http://bugzilla.mozilla.org/show_bug.cgi?id=238945.
            t.match(T_SEMICOLON)
            return n

    elif tt in (T_BREAK, T_CONTINUE):
        n = Node(t)
        if (t.peekOnSameLine() == T_IDENTIFIER):
            t.get()
            n.label = t.token().value
        ss = x.stmtStack
        i = len(ss)
        label = n.label
        if label:
            while True:
                i -= 1
                if (i < 0):
                    raise t.newSyntaxError("Label not found")
                if ss[i].label == label:
                    break
        else:
            while True:
                i -= 1
                if (i < 0):
                    if T_BREAK == tt:
                        raise t.newSyntaxError("Invalid break")
                    else:
                        raise t.newSyntaxError("Invalid continue")
                    # TODO: check -->
                    # do {} while (!ss[i].isLoop && (tt != BREAK || ss[i].ttype != SWITCH))
                if ss[i].isLoop or (tt == T_BREAK and ss[i].ttype == T_SWITCH):
                    break
        n.target = ss[i]

    elif T_TRY == tt:
        n = Node(t)
        n.tryBlock = Block(t, x)
        n.catchClauses = []
        while (t.match(T_CATCH)):
            n2 = Node(t)
            t.mustMatch(T_LEFT_PAREN)
            n2.varName = t.mustMatch(T_IDENTIFIER).value
            if (t.match(T_IF)):
                if (x.ecmaStrictMode):
                    raise t.newSyntaxError("Illegal catch guard")
                if (n.catchClauses > 0 and not n.catchClauses.top().guard):
                    raise t.newSyntaxError("Guarded catch after unguarded")
                n2.guard = Expression(t, x)
            else:
                n2.guard = None
            t.mustMatch(T_RIGHT_PAREN)
            n2.block = Block(t, x)
            n.catchClauses.append(n2)

        if (t.match(T_FINALLY)):
            n.finallyBlock = Block(t, x)
        if (not n.catchClauses and not n.finallyBlock):
            raise t.newSyntaxError("Invalid try statement")
        return n
    
    elif tt in (T_CATCH, T_FINALLY):
        raise t.newSyntaxError(tokens[tt] + " without preceding try")

    elif T_THROW == tt:
        n = Node(t)
        n.exception = Expression(t, x)

    elif T_RETURN == tt:
        if (not x.inFunction):
            raise t.newSyntaxError("Invalid return")
        n = Node(t)
        tt = t.peekOnSameLine()
        if tt not in (T_END, T_NEWLINE, T_SEMICOLON, T_RIGHT_CURLY):
            n.value = Expression(t, x)

    elif T_WITH == tt:
        n = Node(t)
        n.object = ParenExpression(t, x)
        n.body = nest(t, x, n, Statement)
        return n

    elif tt in (T_VAR, T_CONST):
        n = Variables(t, x)

    elif T_DEBUGGER == tt:
        n = Node(t)

    elif tt in (T_NEWLINE, T_SEMICOLON):
        n = Node(t, T_SEMICOLON)
        n.expression = None
        return n

    else:
        if (tt == T_IDENTIFIER):
            t.scanOperand = False
            tt = t.peek()
            t.scanOperand = True
            if (tt == T_COLON):
                label = t.token().value
                ss = x.stmtStack
                for i in range(len(ss)-1, -1, -1):
                    if (ss[i].label == label):
                        raise t.newSyntaxError("Duplicate label")
                t.get()
                n = Node(t, T_LABEL)
                n.label = label
                n.statement = nest(t, x, n, Statement)
                return n

        n = Node(t, T_SEMICOLON)
        t.unget()
        n.expression = Expression(t, x)
        n.end = n.expression.end

    if (t.lineno == t.token().lineno):
        tt = t.peekOnSameLine()
        if tt not in (T_END, T_NEWLINE, T_SEMICOLON, T_RIGHT_CURLY):
            raise t.newSyntaxError("Missing ; before statement")
    t.match(T_SEMICOLON)
    return n

def FunctionDefinition(t, x, requireName, functionForm):
    f = Node(t)
    if (f.ttype != T_FUNCTION):
        if (f.value == "get"):
            f.ttype =  T_GETTER
        else: 
            f.ttype = T_SETTER
    if (t.match(T_IDENTIFIER)):
        f.name = t.token().value
    elif (requireName):
        raise t.newSyntaxError("Missing function identifier")

    t.mustMatch(T_LEFT_PAREN)
    f.params = []
    while True:
        tt = t.get()
        if (tt == T_RIGHT_PAREN):
            break
        if (tt != T_IDENTIFIER):
            raise t.newSyntaxError("Missing formal parameter")
        f.params.append(t.token().value)
        if (t.peek() != T_RIGHT_PAREN):
            t.mustMatch(T_COMMA)

    t.mustMatch(T_LEFT_CURLY)
    x2 = CompilerContext(True)
    f.body = Script(t, x2)
    t.mustMatch(T_RIGHT_CURLY)
    f.end = t.token().end

    f.functionForm = functionForm
    if (functionForm == T_DECLARED_FORM):
        x.funDecls.append(f)
    return f

def Variables(t, x):
    n = Node(t)
    while True:
        t.mustMatch(T_IDENTIFIER)
        n2 = Node(t)
        n2.name = n2.value
        if (t.match(T_ASSIGN)):
            if (t.token().assignOp):
                raise t.newSyntaxError("Invalid variable initialization")
            n2.initializer = Expression(t, x, T_COMMA)
        n2.readOnly = (n.ttype == T_CONST)
        n.append(n2)
        x.varDecls.append(n2)
        if not t.match(T_COMMA):
            break
    return n

def ParenExpression(t, x):
    t.mustMatch(T_LEFT_PAREN)
    n = Expression(t, x)
    t.mustMatch(T_RIGHT_PAREN)
    return n

def oreduce(t, operators, operands):
    n = operators.pop()
    op = n.ttype
    arity = OP_ARITY[op]
    if (arity == -2):
        # Flatten left-associative trees.
        if len(operands) >= 2:
            left = operands[len(operands)-2]
            if (left.ttype == op):
                right = operands.pop()
                left.append(right)
                return left
        arity = 2

    # Always use append to add operands to n, to update start and end.
    a = operands[-arity:]
    del(operands[-arity:])
    for i in range(0, arity):
        n.append(a[i])

    # Include closing bracket or postfix operator in [start,end).
    if (n.end < t.token().end):
        n.end = t.token().end

    operands.append(n)
    return n

class CustomStack(list):
    EMPTY_TOKEN = Token()
    def __init__(self):
        list.__init__(self)

    def top(self):
        l = len(self)
        if l > 0:
            item = list.__getitem__(self, -1)
            return item
        else:
            return self.EMPTY_TOKEN

def Expression(t, x, stop = None):
    n, Id, tt = None, None, None
    operators = CustomStack()
    operands = CustomStack()
    bl = x.bracketLevel
    cl = x.curlyLevel
    pl = x.parenLevel
    hl = x.hookLevel

    while True:
        tt = t.get()
#        print('Expression', int(tt), TOKENS.get(tt))
#        print('Expression', int(tt))
        if (tt == T_END):
            break
#loop:
        if (tt == stop and
            x.bracketLevel == bl and x.curlyLevel == cl and x.parenLevel == pl and
            x.hookLevel == hl):
            # // Stop only if tt matches the optional stop parameter, and that
            # // token is not quoted by some kind of bracket.
            break

        if T_SEMICOLON == tt:
            break # loop
#            // NB: cannot be empty, Statement handled that.

        elif tt in (T_ASSIGN, T_HOOK, T_COLON):
            if (t.scanOperand):
                break# loop
            #// Use >, not >=, for right-associative ASSIGN and HOOK/COLON.
            while (OP_PRECEDENCE.get(operators.top().ttype) > OP_PRECEDENCE[tt] or
                   (tt == T_COLON and operators.top().ttype == T_ASSIGN)):
                oreduce(t, operators, operands)

            if (tt == T_COLON):
                n = operators.top()
                if (n.ttype != T_HOOK):
                    raise t.newSyntaxError("Invalid label")
                x.hookLevel -= 1
            else:
                operators.append(Node(t))
                if (tt == T_ASSIGN):
                    operands.top().assignOp = t.token().assignOp
                else:
                    x.hookLevel += 1      #// tt == HOOK
            t.scanOperand = True

        elif tt in (T_IN, T_COMMA, T_OR, T_AND, T_BITWISE_OR, T_BITWISE_XOR, T_BITWISE_AND, T_EQ, T_NE, T_STRICT_EQ, T_STRICT_NE, T_LT, T_LE, T_GE, T_GT, T_INSTANCEOF, T_LSH, T_RSH, T_URSH, T_PLUS, T_MINUS, T_MUL, T_DIV, T_MOD, T_DOT):
            if T_IN == tt:
                  #// An in operator should not be parsed if we're parsing the head of
                  #// a for (...) loop, unless it is in the then part of a conditional
                  #// expression, or parenthesized somehow.
                  if (x.inForLoopInit and not x.hookLevel > 0 and
                      not x.bracketLevel > 0 and not x.curlyLevel > 0 and not x.parenLevel > 0):
                      break# loop
            if (t.scanOperand):
                break #loop
            while (OP_PRECEDENCE.get(operators.top().ttype) >= OP_PRECEDENCE[tt]):
                oreduce(t, operators, operands)
            if (tt == T_DOT):
                t.mustMatch(T_IDENTIFIER)
                operands.append(Node(t, T_DOT, operands.pop(), Node(t)))
            else:
                operators.append(Node(t))
                t.scanOperand = True

        elif tt in (T_DELETE, T_VOID, T_TYPEOF, T_NOT, T_BITWISE_NOT, T_UNARY_PLUS, T_UNARY_MINUS, T_NOT, T_NEW):
            if (not t.scanOperand):
                break #loop
            operators.append(Node(t))

        elif tt in (T_INCREMENT, T_DECREMENT):
            if (t.scanOperand):
                operators.append(Node(t)) #  // prefix increment or decrement
            else:
                # // Don't cross a line boundary for postfix {in,de}crement.
                if (t.tokens[(t.tokenIndex + t.lookahead - 1) & 3].lineno != t.lineno):
                    break# loop
                  # // Use >, not >=, so postfix has higher precedence than prefix.
                while (OP_PRECEDENCE.get(operators.top().ttype) > OP_PRECEDENCE[tt]):
                    oreduce(t, operators, operands)
                n = Node(t, tt, operands.pop())
                n.postfix = True
                operands.append(n)

        elif T_FUNCTION == tt:
            if (not t.scanOperand):
                break #loop
            operands.append(FunctionDefinition(t, x, False, T_EXPRESSED_FORM))
            t.scanOperand = False

        elif tt in (T_NULL, T_THIS, T_TRUE, T_FALSE, T_IDENTIFIER, T_NUMBER, T_STRING, T_REGEXP):
            if (not t.scanOperand):
                break #loop
            operands.append(Node(t))
            t.scanOperand = False
              
        elif T_LEFT_BRACKET == tt:
            if (t.scanOperand):
                  #// Array initialiser.  Parse using recursive descent, as the
                  #// sub-grammar here is not an operator grammar.
                n = Node(t, T_ARRAY_INIT)
                while True:
                    tt = t.peek()
                    if (tt == T_RIGHT_BRACKET):
                        break
                    if (tt == T_COMMA):
                        t.get()
                        n.append(None)
                        continue
                    n.append(Expression(t, x, T_COMMA))
                    if (not t.match(T_COMMA)):
                        break
                t.mustMatch(T_RIGHT_BRACKET)
                operands.append(n)
                t.scanOperand = False
            else:
                #// Property indexing operator.
                operators.append(Node(t, T_INDEX))
                t.scanOperand = True
                x.bracketLevel += 1

        elif T_RIGHT_BRACKET == tt:
            if (t.scanOperand or x.bracketLevel == bl):
                break# loop
            while (oreduce(t, operators, operands).ttype != T_INDEX):
                continue
            x.bracketLevel -= 1

        elif T_LEFT_CURLY == tt:
            if (not t.scanOperand):
                break #loop
              #// Object initialiser.  As for array initialisers (see above),
              #// parse using recursive descent.
            x.curlyLevel += 1
            n = Node(t, T_OBJECT_INIT)
#          object_init:
            did_break = False
            if not t.match(T_RIGHT_CURLY):
                while True:
                    tt = t.get()
                    if ((t.token().value == "get" or t.token().value == "set") and
                        t.peek() == T_IDENTIFIER):
                        if (x.ecmaStrictMode):
                            raise t.newSyntaxError("Illegal property accessor")
                        n.append(FunctionDefinition(t, x, True, T_EXPRESSED_FORM))
                    else:
                        if tt in (T_IDENTIFIER, T_NUMBER, T_STRING):
                            Id = Node(t)
                        elif tt == T_RIGHT_CURLY:
                            if (x.ecmaStrictMode):
                                raise t.newSyntaxError("Illegal trailing ,")
                            did_break = True
                            break# object_init
                        else:
                            raise t.newSyntaxError("Invalid property name")
                        t.mustMatch(T_COLON)
                        n.append(Node(t, T_PROPERTY_INIT, Id,
                                      Expression(t, x, T_COMMA)))

                    if not t.match(T_COMMA):
                        break

                if not did_break:
                    t.mustMatch(T_RIGHT_CURLY)

            operands.append(n)
            t.scanOperand = False
            x.curlyLevel -= 1

        elif T_RIGHT_CURLY == tt:
            if (not t.scanOperand and x.curlyLevel != cl):
                raise Exception("PANIC: right curly botch")
            break # loop

        elif T_LEFT_PAREN == tt:
            did_break = False
            if t.scanOperand:
                operators.append(Node(t, T_GROUP))
            else:
                while (OP_PRECEDENCE.get(operators.top().ttype) > OP_PRECEDENCE[T_NEW]):
                    oreduce(t, operators, operands)

                #// Handle () now, to regularize the n-ary case for n > 0.
                #// We must set scanOperand in case there are arguments and
                #// the first one is a regexp or unary+/-.
                n = operators.top()
                t.scanOperand = True
                if (t.match(T_RIGHT_PAREN)):
                    if (n.ttype == T_NEW):
                        operators.pop()
                        n.append(operands.pop())
                    else:
                        n = Node(t, T_CALL, operands.pop(), Node(t, T_LIST))

                    operands.append(n)
                    t.scanOperand = False
                    did_break = True
                else:
                    if (n.ttype == T_NEW):
                        n.ttype = T_NEW_WITH_ARGS
                    else:
                        operators.append(Node(t, T_CALL))

            if not did_break:
                x.parenLevel += 1

        elif T_RIGHT_PAREN == tt:
            if (t.scanOperand or x.parenLevel == pl):
                break# loop
            while True:
                tt = oreduce(t, operators, operands).ttype
                if tt in (T_GROUP, T_CALL, T_NEW_WITH_ARGS):
                    break

            if (tt != T_GROUP):
                n = operands.top()
                if (n[1].ttype != T_COMMA):
                    n[1] = Node(t, T_LIST, n[1])
                else:
                    n[1].ttype = T_LIST

            x.parenLevel -= 1

          #// Automatic semicolon insertion means we may scan across a newline
          #// and into the beginning of another statement.  If so, break out of
          #// the while loop and let the t.scanOperand logic handle errors.
        else:
            break# loop

    if (x.hookLevel != hl):
        raise t.newSyntaxError("Missing : after ?")
    if (x.parenLevel != pl):
        raise t.newSyntaxError("Missing ) in parenthetical")
    if (x.bracketLevel != bl):
        raise t.newSyntaxError("Missing ] in index expression")
    if (t.scanOperand):
        raise t.newSyntaxError("Missing operand")

    # // Resume default mode, scanning for operands, not operators.
    t.scanOperand = True
    t.unget()
    while (operators):
        oreduce(t, operators, operands)
    return operands.pop()

class JSParser():
    def __init__(self):
        self.tokenizer = Tokenizer()

    def dumpnodes(self, node):
        print(node)
        for n in node:
            self.dumpnodes(n)

    def parse(self, source, filename = '', line = 0):
        try:
            context = CompilerContext(False)
            self.tokenizer.reset(source, filename, line)
            node = Script(self.tokenizer, context)
            if (not self.tokenizer.done()):
                raise tokenizer.newSyntaxError("Syntax error")
        except JsParseException, e:
            import sys
            sys.stderr.write('%s\n' % e)
            pass

    def parse_file(self, source, filename = '', line = 0):
        try:
            context = CompilerContext(False)
            self.tokenizer.reset(source, filename, line, True)
            node = Script(self.tokenizer, context)
            if (not self.tokenizer.done()):
                raise tokenizer.newSyntaxError("Syntax error")
        except JsParseException, e:
            import sys
            sys.stderr.write('%s\n' % e)
            pass

    def strings(self):
        return self.tokenizer.strings

    def comments(self):
        return self.tokenizer.comments
            
if '__main__' == __name__:
    import sys
    for a in sys.argv[1:]:
        parser = JSParser()
        source = open(a).read()
        node = parser.parse(source, a, 1)
        print('\n'.join([s.encode('ascii', 'ignore') for s in parser.strings()]))
