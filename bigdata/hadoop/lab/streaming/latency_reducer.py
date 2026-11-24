#!/usr/bin/env python3
"""Divide the final grouped sum by its count, once per path."""

import sys

from sum_count_combiner import grouped_totals


try:
    for path, total, count in grouped_totals(sys.stdin):
        print(f"{path}\t{total / count:.2f}")
except ValueError as error:
    sys.exit(str(error))
