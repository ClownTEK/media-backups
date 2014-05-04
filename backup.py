#!/usr/bin/python

import sqlite3
import mmap
import time
import hashlib

_TABLES = ('files',
           'chunks',
           'disks')
_TBL_FIELDS = {
    'files': ('name', 'chunks', 'lastseen'),
    'chunks': ('chunk', 'disks'),
    'disks': ('id', 'label')
    }

def chunks(filename):
  chunklen = 64 * 1024 * 1024
  f = open(filename, 'r')
  m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
  chunks = []
  offset = 0
  while offset < len(m):
    h = hashlib.sha1()
    h.update(m[offset : min(offset + chunklen, len(m))])
    chunks.append(h.hexdigest())
    offset += chunklen
  return chunks


class Backup(object):
  def __init__(self, db_name):
    self.db = sqlite3.connect(db_name)
    c = self.db.cursor()
    for table in _TABLES:
      cur = c.execute('''SELECT name FROM sqlite_master
                                     WHERE type="table" AND name="%s"'''
                                                                  % table)
      if (len(cur.fetchall()) == 0):
        cur = c.execute(('CREATE TABLE %s ("' % table)
                         + '", "'.join(_TBL_FIELDS[table]) + '")')

  def add_file(self, filename):
    c = self.db.cursor()
    cur = c.execute('SELECT name, chunks FROM files WHERE name = "%s"'
                    % filename)
    rows = cur.fetchall()
    if (len(rows) == 0):
      c.execute('INSERT INTO files VALUES ("%s", "", %d)'
          % (filename, int(time.time())))
    else:
      found = False
      chunks = ','.chunks(filename)
      res = c.execute('''UPDATE files SET lastseen = %d
                                WHERE name = "%s" AND chunks = "%s"'''
                      % (int(time.time()), filename, ','.join(chunks)))
      if res.rowcount == 0:
        res = c.execute('''UPDATE files SET lastseen = %d
                                  WHERE name = "%s" AND chunks = ""'''
                        % (int(time.time()), filename))
        if res.rowcount == 0:
          c.execute('INSERT INTO files VALUES ("%s", "", %d)'
              % (filename, int(time.time())))
