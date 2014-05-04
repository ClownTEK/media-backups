#!/bin/bash

die() {
  echo "ERROR: $*"
  exit 1
}

test -f /sbin/cryptsetup || die "Please install cryptsetup."

dev=$1
id=$2

test -n "$dev" || die "Must specify a device."
test -b $dev || die "Can't find '$dev'."
test -n "$id" || die "Must specify id."

label=$(echo "select label from disks where id = $id;" | sqlite3 backup.db)
test -n "$label" || die "Can't find disk."

sudo cryptsetup luksOpen $dev backup$id
test -e /dev/mapper/backup$id || die "Failed to open /dev/mapper/backup$id."
if ! test -d /mnt/b/backup$id; then
  sudo mkdir /mnt/b/backup$id
  echo no | sudo tee /mnt/b/backup$id/LABEL > /dev/null
fi
test $(stat --printf "%m" /mnt/b/backup$id) = / \
  || die "/mnt/b/backup$id shouldn't be mounted on something other than /."
sudo mount /dev/mapper/backup$id /mnt/b/backup$id
test $(stat --printf "%m" /mnt/b/backup$id) = / \
  && die "/mnt/b/backup$id wasn't mounted correctly."
disk_label=$(sudo cat /mnt/b/backup$id/LABEL)
if ! test "$label" = "$disk_label"; then
  die "Mislabeled disk - on disk label is '$disk_label'"
  sudo umount /dev/mapper/backup$id
  sudo cryptsetup luksClose backup$id
fi
