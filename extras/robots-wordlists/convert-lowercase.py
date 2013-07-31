#!/usr/bin/env python
#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2011-2013 RAFT Team
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

# convert wordlist file to lowercase
import sys
import os
from collections import OrderedDict


filenames = []
for arg in sys.argv[1:]:
    if os.path.isfile(arg):
        filenames.append(arg)
    elif os.path.isdir(arg):
        for filename in os.listdir(arg):
            file = os.path.join(arg, filename)
            if os.path.isfile(file):
                filenames.append(file)

for filename in filenames:
    lowercase_list = OrderedDict()
    if filename.endswith('.txt') and 'lower' not in filename:
        lower_filename = filename[:-4] + '-lowercase.txt'
        print((filename, lower_filename))
        for line in open(filename, 'r'):
            lcase = line.lower()
            if lcase not in lowercase_list:
                lowercase_list[lcase] = True
        
        outfile = open(lower_filename, 'w')
        for line in lowercase_list.keys():
            outfile.write(line)
        outfile.close()
        



