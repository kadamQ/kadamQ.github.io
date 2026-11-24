#!/usr/bin/env python3
"""Sum consecutive word groups; input must be sorted/grouped by word."""

import sys


current_word = None
total = 0

for line in sys.stdin:
    record = line.rstrip("\r\n")
    if not record:
        continue
    word, count_text = record.split("\t")
    count = int(count_text)
    if not word or count <= 0:
        raise ValueError("Expected a nonempty word and a positive count")
    if current_word is not None and word != current_word:
        print(f"{current_word}\t{total}")
        total = 0
    current_word = word
    total += count

# No following key arrives to trigger the last group; emit it explicitly.
if current_word is not None:
    print(f"{current_word}\t{total}")
