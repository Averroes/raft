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

import collections
import sys, re

re_counter = re.compile(r'^\d+=>')

def process(file):
    ordered = collections.OrderedDict()
    for line in open(file, 'r'):
        line = line.rstrip()
        if re_counter.search(line):
            pass
        else:
            line = line[1:]
            if line.startswith('/'):
                line = line[1:]
            if line.endswith('/'):
                line = line[:-1]
            fields = line.split('/')
            for field in fields:
                ordered[field] = True

    outfile = file[0:-4]+'.txt'
    output = open(outfile, 'w')
    count = 0
    for k in ordered.keys():
        count += 1
#        output.write('%s\t%s\n' % (k, count))
        output.write('%s\n' % (k))
    output.close()

for file in sys.argv[1:]:
    if not file.endswith('.dat'):
        print('sorry don\'t know what to do with: %s' % file)
    else:
        process(file)

