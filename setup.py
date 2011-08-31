from distutils.core import setup
import sys
import os
import glob

def walk_datalist(obj, dirname, entries):
    if '.svn' in dirname:
        return
    items = []
    for entry in entries:
        if '.svn' != entry:
            filename = os.path.join(dirname, entry)
            if os.path.isfile(filename):
                items.append(filename)
    obj[dirname] = items

def walk_MSVCP90(obj, dirname, entries):
    if obj['found']:
        return
    for entry in entries:
        if entry.lower() == 'msvcp90.dll':
            sys.path.append(dirname)
            obj['found'] = True
            return

def find_MSVCP90():
    obj = {'found': False}
    os.path.walk(os.environ.get('SystemRoot'), walk_MSVCP90, obj)
    if not obj['found']:
        os.path.walk(os.environ.get('ProgramFiles'), walk_MSVCP90, obj)

def get_datafiles():
    datalist = {}
    os.path.walk('thirdparty', walk_datalist, datalist)
    os.path.walk('data', walk_datalist, datalist)
    data_files = []
    keys = datalist.keys()
    keys.sort()
    for key in keys:
        if len(datalist[key]) > 0:
            data_files.append((key, datalist[key]))
    return data_files

if 'darwin' == sys.platform:
    pass
elif 'win32' == sys.platform:
    import py2exe

    find_MSVCP90()
    data_files = get_datafiles()

    setup(
        name = 'RAFT',
        console = ['raft.pyw'],
          data_files = data_files,
          options = {
            'py2exe': 
            {
                'includes': ['lxml.etree', 'lxml._elementpath', 'gzip', 'sip'],
                }
            }
          )
else:
    pass

