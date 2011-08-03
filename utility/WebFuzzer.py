#
# Author: Nathan Hamiel
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
# Utilities for the web fuzzer

import re

# ToDo: Create a source object that contains information about the source matches

class MatchObject(object):
    """ This contains the attributes of a match object for further identification and replacement """
    
    pass

class StandardFuzzer(object):
    """ Standard web fuzzer class """

    def std_fuzz_start(content):
        
        # Determine replacement values and replace
        
        find_sources(content)
    
    def replace_values(content):
        
        # start pattern for named replacement
        sourcePattern = re.compile("\${S_.*}")
        
        match = sourcePattern.search(content)
        # match = re.search("{S_\.*}", content)
        if match:
            variable = match.group().lstrip("${S_")
            print(variable.rstrip("}"))
        else:
            pass
        
    def find_sources(content):
        
        # sourcePattern = re.compile('(\$\{\w+\})')
        # sourcePattern = re.compile('(\$\{\.+\})')
        sourcePattern = re.compile("\$\{.+\}")
        # splitPattern = sourcePattern.split(content)
        sourceSplit = re.compile("=")
        match = sourcePattern.search(content)
        if match:
            sourceValues = match.group()
            
            split = sourceSplit.split(sourceValues)
            print(split)
            
            
            
        # print(splitPattern[0])
        # splitContent = splitPattern[0]
        
def fuzz():
    fuzzer = StandardFuzzer()
    

        