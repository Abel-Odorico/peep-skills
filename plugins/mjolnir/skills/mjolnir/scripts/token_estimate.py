#!/usr/bin/env python3
"""Estimate token cost per file so you load the cheapest useful context first.

Usage:
    python3 token_estimate.py [path] [--top N]

Prints files sorted by estimated tokens (desc), plus a repo total. Estimated
straight from byte size — no file is read — so it's fast and correct even for
huge files. Use before loading: skip the fat, low-relevance ones.
"""
from common import walk_files, estimate_from_size, parse_args


def main():
    pos, opts = parse_args(value_flags=("top",))
    root = pos[0] if pos else "."
    top = int(opts.get("top") or 20)

    rows, total = [], 0
    for path, size in walk_files(root):
        tokens = estimate_from_size(size)
        total += tokens
        rows.append((tokens, path))

    rows.sort(reverse=True)
    print(f"# Mjolnir token estimate — {root}")
    print(f"# files: {len(rows)}   estimated tokens: {total:,}\n")
    print(f"{'TOKENS':>8}  FILE")
    for tokens, path in rows[:top]:
        print(f"{tokens:>8,}  {path}")
    if len(rows) > top:
        rest = sum(t for t, _ in rows[top:])
        print(f"{rest:>8,}  ... {len(rows) - top} more files")


if __name__ == "__main__":
    main()
