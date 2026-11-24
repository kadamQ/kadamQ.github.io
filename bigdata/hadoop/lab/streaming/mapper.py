#!/usr/bin/env python3
"""WordCount mapper: keep the Java lesson's tokenization and letter case."""

import re
import sys


for line in sys.stdin:
    # Java StringTokenizer's default separators: space, tab, LF, CR, form-feed.
    for word in re.findall(r"[^ \t\n\r\f]+", line):
        print(f"{word}\t1")
