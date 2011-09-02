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

from thirdparty.lib import EXIF

from analysis.AbstractAnalyzer import AbstractAnalyzer
from analysis.resultsclasses import ExifExtractorSingleResult

class ExifExtractor(AbstractAnalyzer):
    
    ContentTypeRegex = re.compile("content-type\:.*image\/([j|t]\w+)",re.I)
    
    def __init__(self):
        self.desc="EXIF data from JPG/TIFF image files may contain sensitive personal information (including location)"
        self.friendlyname="EXIF Extractor"
        #print "Loaded the ExifExtractor!"
    
    def analyzeTransaction(self, target, results):
        responseHeaders=target.responseHeaders
        for found in self.ContentTypeRegex.finditer(responseHeaders):
            imageType = found.group(1)
            #print "Found a %s image" % imageType
            f = StringIO.StringIO(target.responseBody)
            tags = EXIF.process_file(f)
            first = True
            output = ""
            for tag in tags.keys():
                if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename','EXIF MakerNote'):
                    if first:
                        first=False
                    else:
                        output+=","
                    output += '"%s":"%s"' % (tag,tags[tag])
            if (len(output) > 0):
                nice_output = "{%s}"%output
                sr = ExifExtractorSingleResult.ExifExtractorSingleResult('EXIF Data', self.desc, nice_output)
                results.addCustomPageResult(pageid=target.responseId,
                                result=sr,
                                url=target.responseUrl)        
            

