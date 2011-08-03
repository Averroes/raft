#
# Attack Payloads - from pywebfuzz
#
# Authors: 
#          Seth Law (seth.w.law@gmail.com)
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

##
# To use:
# from core.fuzzer import AttackPayloads
# xss_attacks = AttackPayloads.AttackPayloads().get_xss_attacks()
# sqli_attacks = AttackPayloads.AttackPayloads().get_sqli_attacks()

class AttackPayloads(object):
    payloads_dir = "data/payloads/"
    sqli_file = "sqli.txt"
    xss_file = "xss.txt"
    sqli_attacks = None
    xss_attacks = None
    
    def __init__(self):
        self.get_sqli_attacks()
        self.get_xss_attacks()
        
    def get_sqli_attacks(self):
        if self.sqli_attacks is None:
            self.sqli_attacks = self.file_read(self.payloads_dir + self.sqli_file)
        return self.sqli_attacks
    
    def get_xss_attacks(self):
        if self.xss_attacks is None:
            self.xss_attacks = self.file_read(self.payloads_dir + self.xss_file)
        return self.xss_attacks
    
    # file_read is modified from pywebfuzz, courtesy of Nathan
    def file_read(self,location):
        """ Read the file contents and return the results. Used in the construction
        of the values for the lists """ 
        file = open(location, "rb")
        vals = list()
    
        for item in file.readlines():
            if item.startswith("# "):
                pass
            else:
                vals.append(item.rstrip())
        
        file.close()
    
        return(vals)
