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

if '__main__' == __name__:

    # This outputs the constants and defintions for JSParser
    # It is more efficient to do this once than everytime the parser is spun up

    DEFINED_tokens = [
        # End of source.
        "END",

        # Operators and punctuators.  Some pair-wise order matters, e.g. (+, -)
        # and (UNARY_PLUS, UNARY_MINUS).
        "\n", ";",
        ",",
        "=",
        "?", ":", "CONDITIONAL",
        "||",
        "&&",
        "|",
        "^",
        "&",
        "==", "!=", "===", "!==",
        "<", "<=", ">=", ">",
        "<<", ">>", ">>>",
        "+", "-",
        "*", "/", "%",
        "!", "~", "UNARY_PLUS", "UNARY_MINUS",
        "++", "--",
        ".",
        "[", "]",
        "{", "}",
        "(", ")",

        # Nonterminal tree node type codes.
        "SCRIPT", "BLOCK", "LABEL", "FOR_IN", "CALL", "NEW_WITH_ARGS", "INDEX",
        "ARRAY_INIT", "OBJECT_INIT", "PROPERTY_INIT", "GETTER", "SETTER",
        "GROUP", "LIST",

        # Terminals.
        "IDENTIFIER", "NUMBER", "STRING", "REGEXP",

        # Keywords.
        "break",
        "case", "catch", "const", "continue",
        "debugger", "default", "delete", "do",
        "else", "enum",
        "false", "finally", "for", "function",
        "if", "in", "instanceof",
        "new", "null",
        "return",
        "switch",
        "this", "throw", "true", "try", "typeof",
        "var", "void",
        "while", "with",
        ]

    # this list has implied precedence
    DEFINED_opTypeNames = (
        ('\n',   "NEWLINE"),
        (';',    "SEMICOLON"),
        (',',    "COMMA"),
        ('?',    "HOOK"),
        (':',    "COLON"),
        ('||',   "OR"),
        ('&&',   "AND"),
        ('|',    "BITWISE_OR"),
        ('^',    "BITWISE_XOR"),
        ('&',    "BITWISE_AND"),
        ('===',  "STRICT_EQ"),
        ('==',   "EQ"),
        ('=',    "ASSIGN"),
        ('!==',  "STRICT_NE"),
        ('!=',   "NE"),
        ('<<',   "LSH"),
        ('<=',   "LE"),
        ('<',    "LT"),
        ('>>>',  "URSH"),
        ('>>',   "RSH"),
        ('>=',   "GE"),
        ('>',    "GT"),
        ('++',   "INCREMENT"),
        ('--',   "DECREMENT"),
        ('+',    "PLUS"),
        ('-',    "MINUS"),
        ('*',    "MUL"),
        ('/',    "DIV"),
        ('%',    "MOD"),
        ('!',    "NOT"),
        ('~',    "BITWISE_NOT"),
        ('.',    "DOT"),
        ('[',    "LEFT_BRACKET"),
        (']',    "RIGHT_BRACKET"),
        ('{',    "LEFT_CURLY"),
        ('}',    "RIGHT_CURLY"),
        ('(',    "LEFT_PAREN"),
        (')',    "RIGHT_PAREN"),
        )

    DEFINED_assignOps = ['|', '^', '&', '<<', '>>', '>>>', '+', '-', '*', '/', '%']

    keywords = {}
    tokens = {}
    assignOps = {}
    defined_globals = {}

    opTypeNames = {}
    opTypeNames_regex = '^'
    first = True
    for name, value in DEFINED_opTypeNames:
        opTypeNames[name] = value
        if '\n' != name:
            if not first:
                opTypeNames_regex += '|^'
            opTypeNames_regex += re.escape(name)
            first = False

    re_first_char = re.compile(r'^[a-z]')
    consts_io = StringIO()
    index = 0
    for token in DEFINED_tokens:
        if re_first_char.match(token):
            name = token.upper()
            keywords[token] = index
        elif opTypeNames.has_key(token):
            name = opTypeNames[token]
        else:
            name = token
        consts_io.write('T_%s = %d\n' % (name, index))
        defined_globals[name] = index
        # crap into our namespace to save some typing
        globals()[name] = index
        tokens[token] = index
        tokens[index] = token
        index += 1

    # mapped assigned operators to index
    index = 0
    for op in DEFINED_assignOps:
        assignOps[op] = tokens[op]

    DEFINED_opPrecedence = {
        SEMICOLON: 0,
        COMMA: 1,
        ASSIGN: 2, HOOK: 2, COLON: 2,
        # The above all have to have the same precedence, see bug 330975.
        OR: 4,
        AND: 5,
        BITWISE_OR: 6,
        BITWISE_XOR: 7,
        BITWISE_AND: 8,
        EQ: 9, NE: 9, STRICT_EQ: 9, STRICT_NE: 9,
        LT: 10, LE: 10, GE: 10, GT: 10, IN: 10, INSTANCEOF: 10,
        LSH: 11, RSH: 11, URSH: 11,
        PLUS: 12, MINUS: 12,
        MUL: 13, DIV: 13, MOD: 13,
        DELETE: 14, VOID: 14, TYPEOF: 14, # PRE_INCREMENT: 14, PRE_DECREMENT: 14,
        NOT: 14, BITWISE_NOT: 14, UNARY_PLUS: 14, UNARY_MINUS: 14,
        INCREMENT: 15, DECREMENT: 15,     # postfix
        NEW: 16,
        DOT: 17,
        }

    opPrecedence = {}
    for k in DEFINED_opPrecedence.keys():
        opPrecedence[k] = DEFINED_opPrecedence[k]

    DEFINED_opArity = {
        COMMA: -2,
        ASSIGN: 2,
        HOOK: 3,
        OR: 2,
        AND: 2,
        BITWISE_OR: 2,
        BITWISE_XOR: 2,
        BITWISE_AND: 2,
        EQ: 2, NE: 2, STRICT_EQ: 2, STRICT_NE: 2,
        LT: 2, LE: 2, GE: 2, GT: 2, IN: 2, INSTANCEOF: 2,
        LSH: 2, RSH: 2, URSH: 2,
        PLUS: 2, MINUS: 2,
        MUL: 2, DIV: 2, MOD: 2,
        DELETE: 1, VOID: 1, TYPEOF: 1,  # PRE_INCREMENT: 1, PRE_DECREMENT: 1,
        NOT: 1, BITWISE_NOT: 1, UNARY_PLUS: 1, UNARY_MINUS: 1,
        INCREMENT: 1, DECREMENT: 1,     # postfix
        NEW: 1, NEW_WITH_ARGS: 2, DOT: 2, INDEX: 2, CALL: 2,
        ARRAY_INIT: 1, OBJECT_INIT: 1, GROUP: 1
        }

    opArity = {}
    for k in DEFINED_opArity.keys():
        opArity[k] = DEFINED_opArity[k]

    print(consts_io.getvalue())
    print('TOKENS = %s\n' % repr(tokens))
    print('OP_TYPE_NAMES = %s\n' % (repr(opTypeNames)))
    print('OP_REGEX = %s\n' % (repr(opTypeNames_regex)))
    print('KEYWORDS = %s\n' % repr(keywords))
    print('ASSIGN_OPS = %s\n' % repr(assignOps))
    print('GLOBAL = %s\n' % repr(defined_globals))
    print('OP_PRECEDENCE = %s\n' % repr(opPrecedence))
    print('OP_ARITY = %s\n' % repr(opArity))

