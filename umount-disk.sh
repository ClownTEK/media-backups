#!/bin/bash

die() {
  echo "ERROR: $*"
  exit 1
}

test -f /sbin/cryptsetup || die "Please install cryptsetup."

id=$1

test -n "$id" || die "Must specify id."

label=$(echo "select label from disks where id = $id;" | sqlite3 backup.db)
test -n "$label" || die "Can't find disk."

test $(stat --printf "%m" /mnt/b/backup$id) = / \
  && die "/mnt/b/backup$id wasn't mounted correctly."
sudo umount /dev/mapper/backup$id
sudo cryptsetup luksClose backup$id
