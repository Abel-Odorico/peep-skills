#!/usr/bin/env python3
"""Audit what context Mjolnir deliberately skipped — so no exclusion silently rots.

Usage:
    python3 harvest.py [path]

When Mjolnir chooses not to load something, it leaves a machine-greppable marker
in code or notes:

    # mjolnir: skipped <what>, load if <trigger>

This harvests every marker into a ledger. A marker with NO "load if" trigger is
flagged `no-trigger` — that's the dangerous kind: an exclusion nobody will ever
revisit. Read-only; prints a ledger and a one-line summary.
"""
import os
import re
import sys
from common import walk_files

MARKER = re.compile(r"mjolnir:\s*(.+)$", re.I)
TRIGGER = re.compile(r"\bload if\b|\bwhen\b|\bif\b", re.I)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    rows, no_trigger = [], 0
    for path, _ in walk_files(root):
        for i, line in enumerate(read_lines(path), 1):
            m = MARKER.search(line)
            if not m:
                continue
            note = m.group(1).strip()
            has_trigger = bool(TRIGGER.search(note))
            if not has_trigger:
                no_trigger += 1
            rows.append((path, i, note, has_trigger))

    if not rows:
        print("# no mjolnir: markers — nothing deferred")
        return
    print(f"# {len(rows)} deferral marker(s):\n")
    for path, line, note, ok in rows:
        flag = "" if ok else "  [no-trigger]"
        print(f"{path}:{line}: {note}{flag}")
    print(f"\n# {len(rows)} markers, {no_trigger} with no revisit trigger")


def read_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.readlines()
    except OSError:
        return []


if __name__ == "__main__":
    main()
