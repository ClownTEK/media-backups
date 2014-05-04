#!/usr/bin/python

import sqlite3
import mmap
import time
import hashlib
import os

_TABLES = {
    'files': ('name', 'chunks', 'lastseen'),
    'chunks': ('chunk', 'disk'),
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
CHUNK = 64 * 1024 * 1024

def makeChunks(filename):
  f = open(filename, 'r')
  m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
  chunks = []
  offset = 0
  while offset < len(m):
    h = hashlib.sha1()
    h.update(m[offset : min(offset + CHUNK, len(m))])
    chunks.append(h.hexdigest())
    offset += CHUNK
  return chunks


class OutOfSpace(Exception):
  pass


class Disks(object):
  def __init__(self, db):
    self.db = db
    self.disks = {}
    cur = self.db.execute('SELECT id, label, confidence FROM disks')
    for (disk_id, label, confidence) in cur.fetchall():
      try:
        f = open('/mnt/b/%s/LABEL' % label, 'r')
        label_text = f.readline().strip()
        if label_text == label:
          self.disks[disk_id] = (label, confidence, f)
      except IOError:
        pass

  def smallestDisk(self, size_needed):
    smallest_size = -1
    for disk_id in self.disks.keys():
      s = os.statvfs('/mnt/b/%s/LABEL' % self.disks[disk_id][0])
      free = s.frsize * s.f_bavail
      if free < size_needed:
        continue
      else:
        if smallest_size == -1 or free < smallest_size:
          smallest_size = free
          smallest_disk = disk_id
    if smallest_size != -1:
      return disk_id
    else:
      raise OutOfSpace('Backup disks full.')

  def storeChunk(self, digest, chunk, size):
    disk_id = self.smallestDisk(size)
    cur = self.db.execute('SELECT * FROM chunks WHERE chunk="%s" AND disk=%d'
                          % (digest, disk_id))
    if len(cur.fetchall()) == 0:
      label = self.disks[disk_id][0]
      chunk_dir = '/mnt/b/%s/%s' % (label, digest[0:2])
      if not os.path.exists(chunk_dir):
        os.mkdir(chunk_dir)
      f = open('%s/%s' % (chunk_dir, digest), 'w')
      f.write(chunk)
      f.flush()
      f.close()
      cur = self.db.execute('INSERT INTO chunks VALUES ("%s", %d)'
                            % (digest, disk_id))

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
    self.disks = Disks(self.db)

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

  def backupNewFiles(self):
    while True:
      cur = self.db.execute(
            'SELECT name FROM files WHERE chunks="" LIMIT 0,10')
      rows = cur.fetchall()
      if len(rows) == 0:
        break
      for row in rows:
        try:
          f = open(row[0], 'r')
          m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
          chunks = []
          offset = 0
          while offset < len(m):
            h = hashlib.sha1()
            extent = min(offset + CHUNK, len(m))
            h.update(m[offset : extent])
            digest = h.hexdigest()
            chunks.append(digest)
            self.disk.storeChunk(m[offset : extent], extent - offset)
            offset += CHUNK
          return chunks
        except IOError:
          self.db.execute('DELETE FROM files WHERE name="%s" AND chunks=""')
