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

import sys, re

from raftparse import raft_parse_xml
import urllib2
from urllib2 import urlparse
import hashlib
import time

unique_hashes = {}
status_counts = {}
user_agents = {}
sitemaps = {}
robot_mappings = {}

re_comment = re.compile(r'^#\s*(.*)')
re_allow = re.compile(r'^(?:#+\s*)?Allow\s*:\s*(.*)', re.I)
re_disallow = re.compile(r'^(?:#+\s*)?Disallow\s*:\s*(.*)', re.I)
re_disallow_broken = re.compile(r'^(?:Dissalow|Disallow)\s*:?\s*(.*)', re.I)
re_sitemap = re.compile(r'^sitemap\s*:\s*(.*)', re.I)
re_useragent = re.compile(r'^(?:ACAP-crawler|User-agent):\s*(.*)', re.I)
re_experimental = re.compile(r'^(?:#+\s*)?(?:noindex|nofollow|noarchive|nopreview):\s*(.*)', re.I)
re_acap_disallow = re.compile(r'^ACAP-disallow-crawl\s*:\s*(.*)', re.I)
re_acap_allow = re.compile(r'^ACAP-allow-crawl\s*:\s*(.*)', re.I)
re_questionable = re.compile(r'^((?:https?:/)?/[-/a-z0-9_\*]+)\s*$', re.I)
# TODO: could parse out host name values
re_host = re.compile(r'^Host\s*:\s*((?:\w+\.)*\w+)', re.I)
re_ignore = re.compile(r'^(?:Visit-time|Request-rate|Crawl-delay)\s*:\s*', re.I)
re_words_splitter = re.compile(r'[^-a-z0-9_.]+', re.I)
re_domain = re.compile(r'(?:^|/)(?:\w+\.)+(?:AC|AD|AE|AERO|AF|AG|AI|AL|AM|AN|AO|AQ|AR|ARPA|AS|ASIA|AT|AU|AW|AX|AZ|BA|BB|BD|BE|BF|BG|BH|BI|BIZ|BJ|BL|BM|BN|BO|BQ|BR|BS|BT|BV|BW|BY|BZ|CA|CAT|CC|CD|CF|CG|CH|CI|CK|CL|CM|CN|CO|COM|COOP|CR|CU|CV|CW|CX|CY|CZ|DE|DJ|DK|DM|DO|DZ|EC|EDU|EE|EG|EH|ER|ES|ET|EU|FI|FJ|FK|FM|FO|FR|GA|GB|GD|GE|GF|GG|GH|GI|GL|GM|GN|GOV|GP|GQ|GR|GS|GT|GU|GW|GY|HK|HM|HN|HR|HT|HU|ID|IE|IL|IM|IN|INFO|INT|IO|IQ|IR|IS|IT|JE|JM|JO|JOBS|JP|KE|KG|KH|KI|KM|KN|KP|KR|KW|KY|KZ|LA|LB|LC|LI|LK|LR|LS|LT|LU|LV|LY|MA|MC|MD|ME|MF|MG|MH|MIL|MK|ML|MM|MN|MO|MOBI|MP|MQ|MR|MS|MT|MU|MUSEUM|MV|MW|MX|MY|MZ|NA|NAME|NC|NE|NET|NF|NG|NI|NL|NO|NP|NR|NU|NZ|OM|ORG|PA|PE|PF|PG|PH|PK|PL|PM|PN|PR|PRO|PS|PT|PW|PY|QA|RE|RO|RS|RU|RW|SA|SB|SC|SD|SE|SG|SH|SI|SJ|SK|SL|SM|SN|SO|SR|ST|SU|SV|SX|SY|SZ|TC|TD|TEL|TF|TG|TH|TJ|TK|TL|TM|TN|TO|TP|TR|TRAVEL|TT|TV|TW|TZ|UA|UG|UK|UM|US|UY|UZ|VA|VC|VE|VG|VI|VN|VU|WF|WS|XXX|YE|YT|ZA|ZM|ZW|INT|ARPA)(?:/|$)', re.I)
re_strip_chars = re.compile(r'[\'\"\\()|@+]')
re_chomp_chars = re.compile(r'[?#;&$%].*$')
re_remove_junk = re.compile(r'/\w+,\w+/|/com\.\w+(\.\w+)*/')
re_remove_comments = re.compile(r'#[^\n]*\n')
re_remove_sitemap = re.compile(r'Sitemap:[^\n]+\n', re.I)
re_reject_spammer = re.compile(r'Disallow:[^\n]*\b(?:adderall|percocet|cialis|OptionARMCalc|ChicagoExperts|ChicagoSellers|ChicagoBuyers|Win\$\d|Loan-Analysis|RealEstateTips|DreamHome)\b', re.I)

matchers = [
#    (re_allow, robot_mappings), 
#    (re_acap_allow, robot_mappings), 
#    (re_disallow, None),
#    (re_acap_disallow, None),
    (re_disallow, robot_mappings),
    (re_acap_disallow, robot_mappings),
    (re_allow, None), 
    (re_acap_allow, None), 
    (re_useragent, None),
    (re_host, None),
    (re_ignore, None),
    (re_experimental, robot_mappings),
    (re_questionable, None),
    (re_disallow_broken, robot_mappings),
    ]

other_content = [
    (re_sitemap, None),
]

reject_content = [
    re.compile(r'/[-0-9_]{8,}|[-0-9_]{8,}\.\w+|Allow:|Disallow:|related-content\.g|related_content_helper\.html|[:<>=]')
]

def initialize_mapcounts(mapcount):
    for name in ['all', 'words', 'files', 'directories', 'extensions']:
        mapcount[name] = {}

def update_entry_count(mapcount, path):
    if not mapcount.has_key(path):
        mapcount[path] = 1
    else:
        mapcount[path] += 1

def normalize_entry(entry):

    if entry.startswith('http://') or entry.startswith('https://'):
        # TODO: could parse out host name values
        splitted = urlparse.urlsplit(entry)
        entry = splitted.path

    entry = urllib2.unquote(entry)
    entry = re_strip_chars.sub('', entry)
    entry = re_chomp_chars.sub('', entry)

    # TODO: could parse out host name values
    entry = re_domain.sub('/', entry)

    entry = re_remove_junk.sub('/', entry)

    # assume garbage
    for rej in reject_content:
        if rej.search(entry):
            return None

    return entry

def add_entry(entry, mapping):

    path = normalize_entry(entry)

    if not path:
        return # useless

    fields = path.split('/')
    dirpath = '/'
    update_entry_count(mapping['directories'], dirpath)
    if path.startswith('/'):
        fields = fields[1:]

    ###print(path, fields)
    add_dir = True
    for i in range(0, len(fields)):
        field = fields[i]
        add_this_one = True
        if '..' in field:
            add_this_one = add_dir = False
        elif '.' in field:
            # assume file (with path_info maybe)
            add_dir = False
            if field.endswith('*'):
                field = field[0:-1]
            if field.startswith('.'):
                filename = field
                ext = ''
                ext2 = ''
            else:
                ndx = field.rindex('.')
                filename = field[0:ndx]
                ext = field[ndx:]
                # look for other
                ndx2 = field.index('.')
                ext2 = field[ndx2:]
            if '*' not in field and len(field) < 20 and not filename.endswith('-') and not filename.startswith('-') and not filename.endswith('_'):
                update_entry_count(mapping['files'], field)
            if len(ext) > 1 and '*' not in ext:
                update_entry_count(mapping['extensions'], ext)
            if ext2 != ext:
                if len(ext2) > 1 and '*' not in ext2:
                    update_entry_count(mapping['extensions'], ext2)
        else:
            this_field = field
            if i < (len(fields) - 1):
                dirpath += field + '/'
                this_field += '/'
            else:
                dirpath += field
            if not field or ('*' in field) or ('..' in field) or len(field) > 16 or field.endswith('-') or field.startswith('-') or (',' in field):
                add_this_one = add_dir = False
            if add_dir:
                update_entry_count(mapping['directories'], dirpath)
            elif add_this_one:
                update_entry_count(mapping['directories'], this_field)
# TODO: support ALL
#        if add_this_one:
#            update_entry_count(mapping['all'], field)

def process(files):
    start_time = time.time()
    count = 0
    duplicates = 0
    skipcount = 0
    for filename in files:
        try:
            tcount, tdup, tskip = process_file(filename)
            count += tcount
            duplicates += tdup
            skipcount += tskip
        except Exception, e:
            import traceback
            sys.stdout.write('ERROR: processing %s\n%s' % (filename, traceback.format_exc(e)))


    sys.stderr.write('\n***processed %d records in %d seconds and ignored %d duplicates and %d skips\n' % (count, int(time.time()-start_time), duplicates, skipcount))

def process_response(host, body, content_type):

    site_mapping = {}
    initialize_mapcounts(site_mapping)

    charset = ''
    if content_type and 'charset=' in content_type:
        charset = content_type[content_type.index('charset=')+8:]
    elif ord(body[0]) > 127:
        charset = 'UTF-8'
    elif ord(body[0]) == 0:
        charset = 'UTF-16'
    if charset:
        try:
            body = body.decode(charset)
            body = body.encode('ascii', 'ignore')
        except Exception, e:
#            sys.stderr.write('ignoring: %s' % (e))
            pass
    comments = ''
    for line in body.splitlines():
        line = line.replace('\xa0', ' ')
        line = line.strip()
        if not line:
            continue
        matched = False
        ndx = line.find('#')
        if 0 == ndx:
            m = re_comment.search(line)
            if m:
                matched = True
                # comments += line + '\n'
            elif comments:
                print(comments)
                comments = ''
        elif ndx > 0:
            line = line[0:ndx].strip()

        for matcher in matchers:
            m = matcher[0].search(line)
            if m:
                matched = True
                mapping = matcher[1]
                if not mapping is None:
                    entry = m.group(1)
                    # TODO: some entries have spaces to list multiple paths ... is this valid?
                    for subentry in entry.split(' '):
                        add_entry(subentry, site_mapping)
                break

        for matcher in other_content:
            m = matcher[0].search(line)
            if m:
                matched = True
                mapping = matcher[1]
                if not mapping is None:
                    entry = m.group(1)
                break

        if not matched and content_type and 'text/plain' in content_type:
            try:
#                sys.stderr.write('unmatched: %s\n' % (line))
                pass
            except UnicodeEncodeError:
                pass

    merge_mappings(site_mapping)

def merge_mappings(site_mapping):
    found_words = {}
    for name in ['all', 'files', 'directories', 'extensions']:
        entries =  site_mapping[name].keys()
        entries.sort()
        entries.reverse()
        for entry in entries:
            include = True
            if '/' == entry:
                include = False
            if site_mapping[name][entry]  <= 2:
                if entry.endswith('/'):
                    pos = entry.rfind('/',0,-1)
                else:
                    pos = entry.rfind('/')
                if pos > -1:
                    this_entry = entry[pos+1:]
                    parent_entry = entry[0:pos+1]
                    if len(this_entry) > 0 and this_entry != parent_entry and site_mapping['directories'].has_key(parent_entry):
                        parent_count = site_mapping['directories'][parent_entry]
#                        print('*** [%s]: %d (%s)' % (parent_entry, parent_count, entry))
                        if  parent_count > 256: # TODO: adjust ?
                            include = False
            if include:
                words = re_words_splitter.split(entry)
                for w in words:
                    if w:
                        if '.' in w and not w.startswith('.'):
                            p1 = 0
                            p0 = w.find('.')
                            while p0 > -1:
                                w2 = w[p1:p0]
                                found_words[w2] = True
                                p1 = p0
                                p0 += 1
                                p0 = w.find('.', p0)
                            w2 = w[p1:]
                            found_words[w2] = True
                        else:
                            found_words[w] = True
                if not robot_mappings[name].has_key(entry):
                    robot_mappings[name][entry] = 1
                else:
                    robot_mappings[name][entry] += 1

    # process words separately
    for word in site_mapping['words'].keys():
        found_words[word] = True

    name = 'words'
    for word in found_words.keys():
        if not robot_mappings[name].has_key(word):
            robot_mappings[name][word] = 1
        else:
            robot_mappings[name][word] += 1

def normalized_robots(body):
    io = StringIO()
    for line in body.splitlines():
        line = line.rstrip()
        n = line.find('#')
        if n > -1:
            line = line[0:n]
        if re_reject_spam.search(line):
            return None
        io.write(line.lower())
    response = io.getvalue()
    io.close()
    return response

def process_file(filename):
    count = 0
    duplicates = 0
    skipcount = 0
    for result in raft_parse_xml(filename):
        origin, host, hostip, url, status, datetime, request, response, method, content_type, extras = result
        
        if status in (200, 206,) and response and response[1]:
            if 'google.' in host or 'blogspot.com' in host:
                pass
            else:
                body = response[1]
                if re_reject_spammer.search(body):
#                    print(body)
                    skipcount += 1
                    continue
                # normalize and calculate hashval
                normalized = body.lower().replace(host, '')
                normalized = re_remove_comments.sub('\n', normalized)
#                normalized = re_remove_sitemap.sub('\n', normalized)
                sha1 = hashlib.sha1()
                sha1.update(normalized)
                hashval = sha1.hexdigest()
                if not unique_hashes.has_key(hashval):
                    unique_hashes[hashval] = True
                    process_response(host, body, content_type)
                    count += 1
                else:
                    duplicates += 1

        if not status_counts.has_key(status):
            status_counts[status] = 1
        else:
            status_counts[status] += 1

    return count, duplicates, skipcount

def print_mapcount(fhandle, cutoff, mapcount):
    count_mapping = {}
    for entry in mapcount.keys():
        count = mapcount[entry]
        if count >= cutoff:
            if not count_mapping.has_key(count):
                count_mapping[count] = [entry]
            else:
                count_mapping[count].append(entry)

    keys = count_mapping.keys()
    keys.sort(key=int)
    keys.reverse()
    for value in keys:
        values = count_mapping[value]
        values.sort()
        fhandle.write('%d=>\n\t%s\n' % (value, '\n\t'.join(values)))

def print_ordered(mapping_name, mapping):
    groupings = [('all', 1), ('large', 2), ('medium', 3), ('small', 4)] # TODO: base on total sizes
#    print('--%s--' % mapping_name)
    for grouping in groupings:
        label, cutoff = grouping
        for name in ['words', 'files', 'directories', 'extensions']:
#            print(' -%s-%s-' % (label, name))
            fhandle = open('raft-%s-%s.dat' % (label, name), 'w')
            print_mapcount(fhandle, cutoff, mapping[name])

for matcher in matchers:
    mapping = matcher[1]
    if mapping is not None:
        initialize_mapcounts(mapping)

files = []
for arg in sys.argv[1:]:
    if arg.startswith('-'):
        pass
    else:
        files.append(arg)

process(files)

for status in status_counts.keys():
    print('status %s: %d' % (status, status_counts[status]))

print_ordered('mappings', robot_mappings)

