#!/usr/bin/env python3.3
#
# RAFT - Response Analysis and Further Testing
#
# Authors: 
#          Nathan Hamiel
#          Gregory Fleischer (gfleischer@gmail.com)
#          Justin Engler
#          Seth Law
#
# Copyright (c) 2011-2013, RAFT Team
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
import os

__version__ = "3.0.1"
__all__ = ['__version__']

def main():

    # TODO: for base Win32, no stdin/stdout

    # for now, just to maintain compatibility
    gui = True
    for arg in sys.argv[1:]:
        if arg == '-new' or arg.endswith('.raftdb'):
            pass
        else:
            # unrecognized or cmd line
            gui = False
            break

    if gui:
        launch_gui()
    else:
        launch_cmd_line()

def launch_gui():
    import RaftGui
    RaftGui.main()

def launch_cmd_line():
    import RaftCmdLine
    RaftCmdLine.main()

if '__main__' == __name__:
    main()


