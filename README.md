# Description

Over the years I've acquired a number of USB disks and USB thumb drives.
I also have a large media server with pictures and music and cdrom iso
images and video files that I could probably recreate, but it would be
long and time consuming.

It's no long practical to back large file servers up to tape, cdroms or
even DVDs. However all the old drives I have from various sources can
store all my media files several times over.

# Backup Method

The overall algorithm works like so:

  * Get a list of all files that need to be backed up.
    Done by: `update-files.py`
  * Split each file into a series of 64 meg chunks and copy
    it to the smallest free backup disk.
  * Track how many copies of each chunk exist.

# Disk Management

Disk quality varies so for each disk assign the disk a confidence value.
Initially I'm assigning 1 to flash drives and 2 to disks.  Decide that
enough copies have been made when a certain confidence threshhold has
been met.  For now I'm kind of partial to 6.

When a disk is full it should be removed and put offsite.  So there
needs to be some alerting there.  The disks are encrypted so offsite
storage should be fine.

These tools manage backup disk lifecycles:

  * `list-disks.sh`: Get a list of known backup disks.
    TODO: Clean up output. Highlight attached disks and report
          storage levels. Record last known storage levels for
          unattached disks.
  * `add-disk.sh`: Adds a new disk to the backup pool.
  * `mount-disk.sh`: Mounts an existing disk.
    TODO: Remove chunks that are no longer in use.
  * `rm-disk.sh`: Remove disk from storage pool.
    TODO: Remove chunks that were on that disk and update files.
  * `umount-disk.sh`: Unmount a backup disk.
    TODO: Record its storage levels.

# TODO

  * Hardcoded to my needs. Everything needs to go into a config file.
  * Shell scripts probably need to evolve to python scripts.
  * Chunk distribution - currently do the initial backups of a chunk to
    a single disk.  Need to add to that and distribute chunks till a
    confidence level of 6 is reached.
  * Compression?
  * An fsck for backup disks.  Confirm checksums (filenames) match
    file contents.
  * Database access is really limited.  How does one make sqlite db
    access less exclusive?
  * Should store file meta info to limit need to recalc sha1 sums.
  * Some way to request disks be removed while backup-files.py is
    running.
  * Store chunk size info.
  * Store disk size info.
