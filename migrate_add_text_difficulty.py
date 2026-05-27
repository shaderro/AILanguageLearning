#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legacy entry: runs backfill_preset_text_metadata (difficulty + exam_content)."""

import subprocess
import sys

if __name__ == '__main__':
    raise SystemExit(subprocess.call([sys.executable, 'backfill_preset_text_metadata.py', *sys.argv[1:]]))
