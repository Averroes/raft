#!/usr/bin/env python
# convert wordlist file to lowercase
import sys
from collections import OrderedDict

for filename in sys.argv[1:]:
    lowercase_list = OrderedDict()
    if filename.endswith('.txt') and 'lower' not in filename:
        lower_filename = filename[:-4] + '-lowercase.txt'
        print(filename, lower_filename)
        for line in open(filename, 'r'):
            lcase = line.lower()
            if not lowercase_list.has_key(lcase):
                lowercase_list[lcase] = True
        
        outfile = open(lower_filename, 'w')
        for line in lowercase_list.iterkeys():
            outfile.write(line)
        outfile.close()
        



