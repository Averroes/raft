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

from analysis.resultsclasses import SingleResult

class ExifExtractorSingleResult(SingleResult.SingleResult):
    
    def toHTML(self):
        #print "EXIFEXTRACTOR!!!"
        locationtext=''
        dataoutput=''
        if self.span is not None:
            locationtext='%s to %s'%self.span
        
        try: 
        #datalist = ast.literal_eval(self.data)
        #dataoutput = '<ol><li>%s</li></ol>' % self.data
            dataoutput = "<ol>"
            for k in self.data.keys():
                dataoutput += "<li>%s: %s</li>" % (k,self.data[k])
            dataoutput += '</ol>'
        except ValueError:
            print("ValueError: %s" % self.data)
        except:
            print("Error occurred on this data: %s" % self.data)

        NiceOutput="""
        <h3>%s</h3><br>
        <font size="-1">Custom toHTML() | Severity: <b>%s</b> | Certainty: <b>%s | Location: %s</b></font>
        <p><b>Description:</b>
        <ul>
         <li>%s</li>
        </ul>
        <p><b>More Details:</b>
        <li>
         <ul>%s</ul>
        </li>
        """%(self.type,
               SingleResult.SingleResult.SEVERITYNAME[self.severity],
               SingleResult.SingleResult.SEVERITYNAME[self.certainty],
               locationtext,
               self.desc,
               dataoutput)
                
        return NiceOutput
