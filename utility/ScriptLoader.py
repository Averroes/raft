#
# Functionality to dynamically load Python scripts from files and strings
#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2013 RAFT Team
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

import sys

class ScriptEnv():
    def __init__(self, global_ns = None, local_ns = None):
        self.valid = True
        self.instance = False
        self.functions = {}
        self._properties = {}
        if global_ns is None:
            self.global_ns = {}
        else:
            self.global_ns = global_ns
        if local_ns is None:
            self.local_ns = self.global_ns
        else:
            self.local_ns = local_ns

    def __getitem__(self, name):
        return self._properties[name]

    def __setitem__(self, name, value):
        self._properties[name] = value

class ScriptLoader():
    def __init__(self):
        pass

    def load_from_string(self, python_code, global_ns = None, local_ns = None):
        script_env = ScriptEnv(global_ns, local_ns)
        self.load_python_code(script_env, python_code)
        return script_env

    def load_from_file(self, filename, global_ns = None, local_ns = None):
        fh = open(filename, 'rb')
        python_code = fh.read()
        fh.close()
        script_env = ScriptEnv(global_ns, local_ns)
        self.load_python_code(script_env, python_code)
        return script_env

    def load_python_code(self, script_env, python_code):
        try:
            compiled = compile(python_code, '<string>', 'exec')
            exec(compiled, script_env.global_ns, script_env.local_ns)
            for key in script_env.local_ns:
                value = script_env.local_ns[key]
                if str(type(value)) == "<class 'type'>":
                    instance = value()
                    script_env.instance = instance
                    for item in dir(instance):
                        if not item.startswith('_'):
                            itemvalue = getattr(instance, item)
                            if str(type(itemvalue)) == "<class 'method'>":
                                script_env.functions[item] = itemvalue
                elif str(type(value)) == "<class 'function'>":
                    script_env.functions[key] = value

        except Exception as error:
            sys.stderr.write('Exception loading code: %s\n' % (error))
            raise
        
if '__main__' == __name__:
    import sys
    import os
    arg = sys.argv[1]
    scriptLoader = ScriptLoader()
    if os.path.exists(arg):
        filename = arg
        script_env = scriptLoader.load_from_file(filename)
    else:
        script_env = scriptLoader.load_from_string(arg)

    print(script_env.functions)
