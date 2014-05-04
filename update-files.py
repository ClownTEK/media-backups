#!/usr/bin/python

import backup
import os

EXCLUDE_DIRS = ('.AppleDouble', '.svn')
EXCLUDE_FILES = ('._.DS_Store', '.DS_Store')

bkup = backup.Backup('backup.db')
root_dirs = ('/u2', '/u4')
for root_dir in root_dirs:
  for dir_name, subdirs, files in os.walk(root_dir):
    subdirs[:] = [d for d in subdirs if d not in EXCLUDE_DIRS]
    files[:] = [f for f in files if f not in EXCLUDE_FILES]
    for fname in files:
      print('%s' % os.path.join(dir_name, fname))
      bkup.addFile(fname)
