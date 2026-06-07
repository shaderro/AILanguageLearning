#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legacy entry: runs backfill_preset_text_metadata (difficulty + exam_content)."""

import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if __name__ == '__main__':
    raise SystemExit(subprocess.call([sys.executable, 'backfill_preset_text_metadata.py', *sys.argv[1:]]))
