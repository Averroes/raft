#
# Author: Seth Law
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
import StringIO
import os
import sys
import struct

from ...AbstractAnalyzer import AbstractAnalyzer


class GIFComments(AbstractAnalyzer):
    
    ContentTypeRegex = re.compile("content-type\:.*image\/([gif]\w+)",re.I)
    
    def __init__(self):
        self.desc="Determine existence of and display GIF Image comments"
        self.friendlyname="GIF Comment Analyzer"
        #print "Loaded the GCA!"
    
    def analyzeTransaction(self, target, results):
        responseHeaders=target.responseHeaders
        for found in self.ContentTypeRegex.finditer(responseHeaders):
            imageType = found.group(1)
            #print "Found a %s image" % imageType
            data = target.responseBody
            f = StringIO.StringIO(data)
            comments = self.extract_comments(f)
            if (comments != None):
                #print "GIF Comment: %s" % comments
            
                CommentsRegex = re.compile(comments)
                for match in CommentsRegex.finditer(data):
                    results.addPageResult(pageid=target.responseId, 
                                  url=target.responseUrl,
                                  type='Sensitive Data',
                                  desc='GIF Comment was found.',
                                  data={'GIF Comment':comments},
                                  span=match.span(),
                                  highlightdata=comments)
            
    def extract_comments(self,fobj):  
        giftype = fobj.read(6)
        pf = struct.unpack('<hhBBB', fobj.read(7))[2]
        if pf & 0x80:
            pallete_size = 2 << (pf & 0x07)
            fobj.read(3 * pallete_size)
        # finished reading header

        fsize = fobj.len
        while fobj.tell() != fsize:
            mark = ord(fobj.read(1))

            label = None
            if mark == 0x21: # gif extension
                #print "Found an Extension!"
                label = ord(fobj.read(1))
                is_comment = 254

        # read the extension block
                blocksize = ord(fobj.read(1))
                #print "Blocksize = %d" % blocksize
                while blocksize:
                    if is_comment == label:
                        return fobj.read(blocksize)
                    else:
                        fobj.read(blocksize)

                    if fobj.tell() != fsize: 
                        blocksize = ord(fobj.read(1))
                    else:
                        blocksize = None
        return None