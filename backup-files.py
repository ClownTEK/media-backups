#!/usr/bin/python

import backup
import os
import sys

bkup = backup.Backup('backup.db')
bkup.backupNewFiles()
