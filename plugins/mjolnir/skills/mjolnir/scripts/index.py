#!/usr/bin/env python3
"""Build a Level 0 project index — a cheap map of the repo without loading it.

Usage:
    python3 index.py [path]

Emits a compact directory tree with per-folder file counts and token estimates.
This is the FIRST thing to load in a large repo: it costs ~a few hundred tokens
and tells you where the relevant code lives, so you never dump whole trees.
Estimates come from byte size — no file is read.
"""
import os
from common import (IGNORE_DIRS, is_ignored, is_sensitive, estimate_from_size,
                    parse_args)


def main():
    pos, _ = parse_args()
    root = os.path.abspath(pos[0] if pos else ".")
    folder_tokens, folder_files, total = {}, {}, 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in IGNORE_DIRS and not (d.startswith(".") and d != ".github")]
        rel = os.path.relpath(dirpath, root)
        tokens = count = 0
        for name in filenames:
            full = os.path.join(dirpath, name)
            if is_ignored(dirpath, name) or is_sensitive(full):
                continue
            try:
                tokens += estimate_from_size(os.path.getsize(full))
            except OSError:
                continue
            count += 1
        if count:
            folder_tokens[rel] = tokens
            folder_files[rel] = count
            total += tokens

    print(f"# Mjolnir index — {root}")
    print(f"# total estimated tokens: {total:,}\n")
    for rel in sorted(folder_tokens):
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        indent = "  " * depth
        label = os.path.basename(rel) + "/" if rel != "." else "./"
        print(f"{indent}{label}  ({folder_files[rel]} files, ~{folder_tokens[rel]:,} tok)")


if __name__ == "__main__":
    main()
