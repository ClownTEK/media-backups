#!/bin/bash

die() {
  echo "ERROR: $*"
  exit 1
}

test -f /sbin/cryptsetup || die "Please install cryptsetup."

dev=$1
id=$2
confidence=$3
user=$(whoami)

test -n "$dev" || die "Must specify a device."
test -b $dev || die "Can't find '$dev'."
test -n "$id" || die "Must specify id."
test -n "$confidence" \
  || die "Must specify confidence (1 for flash, 2 for disk)"

if [[ $(($(sudo blockdev --getsize64 $dev) / 1024 / 1024 / 64)) < 100 ]]; then
  bytes_per_inode=4096
else
  bytes_per_inode=$((16 * 1024 * 1024))
fi
echo "insert into disks values ($id, 'backup$id', $confidence);" \
  | sqlite3 backup.db || die "Failed to add to backup db."

sudo cryptsetup -v -y luksFormat $dev
sudo cryptsetup luksOpen $dev backup$id
test -e /dev/mapper/backup$id || die "Failed to open /dev/mapper/backup$id."
sudo mkfs.ext4 -m 0 -i $bytes_per_inode /dev/mapper/backup$id
test -d /mnt/b/backup$id \
  || sudo mkdir /mnt/b/backup$id
test $(stat --printf "%m" /mnt/b/backup$id) = / \
  || die "/mnt/b/backup$id shouldn't be mounted on something other than /."
echo no | sudo tee /mnt/b/backup$id/LABEL > /dev/null
sudo mount /dev/mapper/backup$id /mnt/b/backup$id
test $(stat --printf "%m" /mnt/b/backup$id) = / \
  && die "/mnt/b/backup$id wasn't mounted correctly."
echo backup$id | sudo tee /mnt/b/backup$id/LABEL > /dev/null
sudo chown -R ${user}:$user /mnt/b/backup$id
sudo umount /dev/mapper/backup$id
sudo cryptsetup luksClose backup$id
