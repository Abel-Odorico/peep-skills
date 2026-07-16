#!/usr/bin/env python3
"""Concept search that returns the enclosing SYMBOL per hit, not raw grep lines.

    python3 find.py <term> [path] [--top N]

Grep dumps matched lines with no structure; you then read files to see what they
belong to. find reports, per match, the function/class it lives in — so you see
where a concept lives as a handful of symbols instead of a wall of lines.
Deduped by (file, symbol) and capped.
"""
import os
import re
from common import walk_files, read_text, parse_args
import symbols as S

SRC_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".php",
           ".go", ".rb", ".rs", ".java", ".vue", ".svelte"}


def enclosing(syms, lineno):
    """Nearest symbol defined at or before this line."""
    best = None
    for sline, sig in syms:
        if sline <= lineno:
            best = (sline, sig)
        else:
            break
    return best


def main():
    pos, opts = parse_args(value_flags=("top",))
    if not pos:
        print(__doc__)
        return
    term = pos[0]
    root = pos[1] if len(pos) > 1 else "."
    top = int(opts.get("top") or 30)
    rx = re.compile(re.escape(term), re.I)

    seen, rows = set(), []
    for path, _ in walk_files(root):
        if os.path.splitext(path)[1] not in SRC_EXT:
            continue
        text = read_text(path)
        if not rx.search(text):
            continue
        syms = S.extract(path)
        for i, line in enumerate(text.splitlines(), 1):
            if not rx.search(line):
                continue
            enc = enclosing(syms, i)
            label = enc[1] if enc else "(module scope)"
            key = (path, label)
            if key in seen:
                continue
            seen.add(key)
            rows.append((path, enc[0] if enc else i, label, line.strip()[:100]))

    print(f"# '{term}' — {len(rows)} symbol(s) across the repo\n")
    for path, lineno, label, snippet in rows[:top]:
        print(f"{path}:{lineno}: {label}")
        print(f"    ↳ {snippet}")
    if len(rows) > top:
        print(f"\n… +{len(rows) - top} more symbols (narrow the term or --top N)")


if __name__ == "__main__":
    main()
