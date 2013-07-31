#!/usr/bin/env python
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

import zipfile, sys, collections, re, bz2
import time
from pybloom import BloomFilter

class MergeTopSites:
    def __init__(self, args):
        self.merged = BloomFilter(capacity = 1800000, error_rate=0.001)
        self.re_alexa_skip = re.compile(r'/|\.(?:blogspot|wordpress|blogsome|blogspirit|typepad|homestead|posterous|splinder|blogs|ning|blogdetik|weebly|blogware|webs|journalspace)\.com')
        self.re_digits = re.compile(r'^\d+$')
        self.output = None
        self.tcount = 0
        self.ocount = 0

        self.alexa_file = args[0]
        self.quantcast_file = args[1]
        self.outfile = args[2]

        self.open_output()

    def process_value(self, hostname, re_skip = None):
        if re_skip and re_skip.search(hostname):
            return
        if not self.merged.add(hostname):
            self.output.write('%s\n' % (hostname))
            self.ocount += 1

    def open_zip(self, filename):
        zfile = zipfile.ZipFile(filename, 'r')
        zi = zfile.infolist()
        file = zfile.open(zi[0])
        return file

    def process(self):
        t0 = time.time()
        self.process_files([(self.alexa_file, self.re_alexa_skip, ','), (self.quantcast_file, None, '\t')])
        print(('processed [%d] records and output [%d] records in %d seconds' % (self.tcount, self.ocount, int(time.time()-t0))))
        
    def process_files(self, entries):

        flist = []
        rlist = []
        slist = []
        completed = []
        for entry in entries:
            flist.append(self.open_zip(entry[0]))
            rlist.append(entry[1])
            slist.append(entry[2])
            completed.append(False)

        count = 0
        ecount = len(flist)
        ccount = 0
        while True:
            index = count % ecount
            count += 1
            if completed[index]:
                continue
            line = flist[index].readline()
            if not line:
                completed[index] = True
                ccount += 1
                if ccount == ecount:
                    break
                continue
            sc = slist[index]
            line = line.rstrip()
            if line.startswith('#'):
                continue
            if sc in line:
                fields = line.split(sc)
                if self.re_digits.search(fields[0]):
                    self.tcount += 1
                    self.process_value(fields[1], rlist[index])

    def open_output(self):
        if self.outfile.endswith('.bz2'):
            self.output = bz2.BZ2File(self.outfile, 'w')
        else:
            self.output = open(self.outfile, 'wb')

if '__main__' == __name__:
    if len(sys.argv) != 4:
        sys.stderr.write('usage: %s <alexa> <quantcast> <output>\n' % (sys.argv[0]))
        sys.exit(1)

    merger = MergeTopSites(sys.argv[1:])
    merger.process()
