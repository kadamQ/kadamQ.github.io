#!/usr/bin/env python3
"""Map single-line CSV records to path TAB duration_sum TAB count."""

import csv
import re
import sys
import unicodedata


for line in sys.stdin:
    try:
        # Parse each physical line independently: multiline CSV is unsupported.
        fields = next(csv.reader([line], strict=True))
        if fields == ["path", "response_ms"]:
            continue
        if len(fields) != 2:
            raise ValueError("Expected two fields")
        path, duration_text = fields
        if not path.startswith("/") or any(
            unicodedata.category(char) == "Cc" for char in path
        ):
            raise ValueError("Invalid path")
        if re.fullmatch(r"[0-9]+", duration_text) is None:
            raise ValueError("Expected nonnegative integer milliseconds")
        duration = int(duration_text)
    except (csv.Error, ValueError):
        print("reporter:counter:StreamingLab,InvalidRecord,1", file=sys.stderr)
        continue
    print(f"{path}\t{duration}\t1")
