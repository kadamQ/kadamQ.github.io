#!/usr/bin/env python3
"""Combine sorted (path, sum, count) records without computing an average."""

import re
import sys
import unicodedata


def grouped_totals(lines):
    """Yield one validated (path, total, count) for each consecutive key group."""
    current_path = None
    total = count = 0
    for line_number, line in enumerate(lines, 1):
        record = line.rstrip("\r\n")
        if not record:
            continue
        fields = record.split("\t")
        error = f"Invalid intermediate record at line {line_number}"
        if len(fields) != 3:
            raise ValueError(error)
        path, sum_text, count_text = fields
        if (
            not path.startswith("/")
            or any(unicodedata.category(char) == "Cc" for char in path)
            or re.fullmatch(r"[0-9]+", sum_text) is None
            or re.fullmatch(r"[0-9]+", count_text) is None
        ):
            raise ValueError(error)
        partial_sum, partial_count = int(sum_text), int(count_text)
        if partial_count <= 0:
            raise ValueError(error + ": count must be positive")
        if current_path is not None and path != current_path:
            yield current_path, total, count
            total = count = 0
        current_path = path
        total += partial_sum
        count += partial_count
    if current_path is not None:
        yield current_path, total, count


if __name__ == "__main__":
    try:
        for path, total, count in grouped_totals(sys.stdin):
            print(f"{path}\t{total}\t{count}")
    except ValueError as error:
        sys.exit(str(error))
