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

from io import StringIO, BytesIO
import binascii
import re

class HexDump():
    def __init__(self):
        self.re_hex_items = re.compile(r'([0-9A-Fa-f]{2})')
        self.re_hex_block = re.compile(r'^(?:[0-9A-Fa-f]{8} \| )?([0-9A-Fa-f ]*?)(?: \| .*)?$')

    def dump(self, data):
        """ Convert bytes to a hex dump format block """
        sio = StringIO()
        for count in range(0, len(data), 16):
            b = data[count:count+16]
            h = binascii.b2a_hex(b)
            items = self.re_hex_items.findall(h.decode('ascii'))
            display = ' '.join(items)
            aio = StringIO()
            for i in items:
                o = ord(binascii.a2b_hex(i))
                if 31 < o < 127:
                    aio.write(chr(o))
                else:
                    aio.write('.')
            ascii_display = aio.getvalue()
            sio.write('%08X | %-47s | %s\n' % (count, display, ascii_display))

        return sio.getvalue()

    def undump(self, hexblock):
        """ Convert a hex dump block format to bytes """
        bio = BytesIO()
        for line in hexblock.splitlines():
            m = self.re_hex_block.match(line)
            if not m:
                raise Exception('unexpected line for block format: [%s]' % (line))
            block = m.group(1)
            asc = block.replace(' ', '')
            bio.write(binascii.a2b_hex(asc))
    
        return bio.getvalue()
           

if '__main__' == __name__:
    import sys
    import hashlib

    f = open(sys.argv[1], 'rb')
    data = f.read()
    h1 = hashlib.md5(data).hexdigest()
    hd = HexDump()
    x = hd.dump(data)
    print(x)
    b = hd.undump(x)
    h2 = hashlib.md5(b).hexdigest()

    print(h1)
    print(h2)
