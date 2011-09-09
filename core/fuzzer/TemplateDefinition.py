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

from TemplateItem import TemplateItem

class TemplateDefinition(object):

    def __init__(self, template_text):
        self.re_word = re.compile('\w')
        self.re_space = re.compile('\s')
        self.template_items = []
        self.parameter_names = set()
        self.function_names = set()

        self.__crack(template_text)

    def __crack(self, template_text):

        # lex and scan
        current_item = self.template_items
        current_io = StringIO()
        have_dollar, have_parameter, have_function, have_definition = False, False, False, False
        paren_stack = []
        state_stack = []
        lineno = 0

        for c in template_text:
            if have_parameter:
                if '}' == c:
                    # finished
                    have_parameter = False
                    current_value = current_io.getvalue()
                    if current_value in ["method", "request_uri", "global_cookie_jar", "user_agent", "host"]:
                        current_item.append(TemplateItem(current_value, TemplateItem.T_BUILTIN))
                    else:
                        self.parameter_names.add(current_value)
                        current_item.append(TemplateItem(current_value, TemplateItem.T_PAYLOAD))
                    current_io = StringIO()
                elif self.re_word.match(c):
                    current_io.write(c)
                elif self.re_space.match(c):
                    pass
                else:
                    raise Exception('invalid template parameter:' + c)
            elif have_function:
                if ')' == c:
                    # finished
                    have_function = False
                elif self.re_word.match(c):
                    current_io.write(c)
                elif self.re_space.match(c):
                    pass
                elif '(' == c:
                    # found function definition
                    current_value = current_io.getvalue()
                    if not current_value:
                        raise Exception('invalid function definition')
                    self.function_names.add(current_value)
                    next_item = TemplateItem(current_value, TemplateItem.T_FUNCTION)
                    current_item.append(next_item)
                    current_io = StringIO()
                    state_stack.append((current_item, current_io, have_dollar, have_parameter, have_function, have_definition, paren_stack))
                    paren_stack = []
                    current_item = next_item
                    current_io = StringIO()
                    have_dollar, have_parameter, have_function = False, False, False
                    have_definition = True
                else:
                    raise Exception('invalid template parameter in function:' + c)

            elif have_dollar:
                if '(' == c:
                    have_function = True
                    have_dollar = False
                    current_value = current_io.getvalue()
                    if current_value:
                        current_item.append(TemplateItem(current_value, TemplateItem.T_TEXT))
                        current_io = StringIO()
                elif '{' == c:
                    have_parameter = True
                    have_dollar = False
                    current_value = current_io.getvalue()
                    if current_value:
                        current_item.append(TemplateItem(current_value, TemplateItem.T_TEXT))
                        current_io = StringIO()
                else:
                    # regular dollar
                    have_dollar = False
                    current_io.write('$')
                    current_io.write(c)
            elif '$' == c:
                have_dollar = True
            elif '(' == c and have_definition:
                paren_stack.append(c)
                current_io.write(c)
            elif ')' == c and have_definition:
                if len(paren_stack) > 0:
                    paren_stack.pop()
                    current_io.write(c)
                else:
                    current_value = current_io.getvalue()
                    if current_value:
                        current_item.append(TemplateItem(current_value, TemplateItem.T_TEXT))
                    current_item, current_io, have_dollar, have_parameter, have_function, have_definition, paren_stack = state_stack.pop()
            else:
                current_io.write(c)

        if 0 != len(state_stack):
            raise Exception('stack error: %s' %  repr(state_stack))

        current_value = current_io.getvalue()
        if current_value:
            current_item.append(TemplateItem(current_value, TemplateItem.T_TEXT))

