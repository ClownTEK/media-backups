#!/bin/bash

test -n "$1" || exit 1

echo "delete from disks where id = $1;" | sqlite3 backup.db
