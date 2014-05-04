#!/usr/bin/python

import sqlite3
import mmap
import time
import hashlib

_TABLES = {
    'files': ('name', 'chunks', 'lastseen', 'confidence'),
    'chunks': ('chunk', 'disks'),
    'disks': ('id', 'label', 'confidence')
    }
_INDEXES = {
    'files1': 'create unique index files1 on files (name, chunks)',
    'files2': 'create index files2 on files (lastseen)',
    'chunks1': 'create unique index chunks1 on chunks (chunk)',
    'disks1': 'create unique index disks1 on disks (id)',
    }
STATE_CHAR = {
    'new': '+',
    'backed up': '@',
    'seen': '.',
    'newer': '*'
    }

def makeChunks(filename):
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
    self.db = sqlite3.connect(db_name, isolation_level=None)
    for table, fields in _TABLES.iteritems():
      cur = self.db.execute('''SELECT name FROM sqlite_master
                                      WHERE type="table" AND name="%s"'''
                                                                   % table)
      if (len(cur.fetchall()) == 0):
        self.db.execute(('CREATE TABLE %s ("' % table)
                         + '", "'.join(fields) + '")')
    for index, command in _INDEXES.iteritems():
      cur = self.db.execute('''SELECT name FROM sqlite_master
                                      WHERE type="index" AND name="%s"'''
                                                                   % index)
      if (len(cur.fetchall()) == 0):
        self.db.execute(command)

  def addFile(self, filename):
    cur = self.db.execute('SELECT name, chunks FROM files WHERE name = "%s"'
                          % filename)
    rows = cur.fetchall()
    if len(rows) == 0:
      self.db.execute('INSERT INTO files VALUES ("%s", "", %d)'
                      % (filename, int(time.time())))
      state = 'new'
    else:
      if len(rows) == 1 and rows[0][1] == '':
        res = self.db.execute('''UPDATE files SET lastseen = %d
                                        WHERE name = "%s" AND chunks = ""'''
                              % (int(time.time()), filename))
        state = 'seen'
      else:
        chunks = ','.join(makeChunks(filename))
        res = self.db.execute('''UPDATE files SET lastseen = %d
                                  WHERE name = "%s" AND chunks = "%s"'''
                        % (int(time.time()), filename, ','.join(chunks)))
        state = 'backed up'
        if res.rowcount == 0:
          res = self.db.execute('''UPDATE files SET lastseen = %d
                                          WHERE name = "%s" AND chunks = ""'''
                                % (int(time.time()), filename))
          state = 'seen'
          if res.rowcount == 0:
            self.db.execute('INSERT INTO files VALUES ("%s", "", %d)'
                            % (filename, int(time.time())))
            state = 'newer'
    return state
