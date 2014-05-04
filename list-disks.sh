#!/bin/bash

echo 'select * from disks;' | sqlite3 backup.db
