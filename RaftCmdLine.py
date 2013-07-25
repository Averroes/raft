#
# Class that exposes the command line functionality
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

from raft import __version__

def main():
    sys.stdout.write('\nRaftCmdLine - version: %s\n' %  (__version__))
    sys.stdout.write('''
    
    Howdy!

    Thanks for trying RAFT 3.

    You'll want to know this is a special pre-release version for the Arsenal at Blackhat USA 2013.
    Some of the features are not implemented, or have compatibility issues we are working to fix.

    Before you start doing any real work, you'll want to get the latest version of the tool from:

    http://code.google.com/p/raft/

    Have Fun!

''')

if '__main__' == __name__:
    main()
