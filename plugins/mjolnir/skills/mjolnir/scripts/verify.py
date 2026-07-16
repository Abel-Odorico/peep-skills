#!/usr/bin/env python3
"""Prove a lossy pass (summary, symbol extraction, compression) kept what matters.

Usage:
    python3 verify.py <original> <compressed>

Compares the two and classifies drift as ERROR (must-keeps lost → the compressed
version is unsafe, roll back to original) or WARN (cosmetic, allowed). Exit code
1 on any ERROR so a caller can gate on it.

Must-keeps (ERROR if lost): URLs, fenced code blocks, inline-code tokens
(multiplicity-aware — losing one of three identical tokens still fails).
Soft (WARN only): file paths, heading count.
"""
import re
import sys
from collections import Counter

URL = re.compile(r"https?://[^\s)>\]]+")
FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"`[^`\n]+`")
PATH = re.compile(r"(?:\./|\.\./|/)?[\w\-]+(?:/[\w\-.]+)+")
HEADING = re.compile(r"^#{1,6}\s", re.M)


def read(p):
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    orig, comp = read(sys.argv[1]), read(sys.argv[2])

    errors, warns = [], []

    # Fenced code first, then remove it so inline check ignores code inside fences.
    o_fence, c_fence = FENCE.findall(orig), FENCE.findall(comp)
    if Counter(o_fence) != Counter(c_fence):
        lost = list((Counter(o_fence) - Counter(c_fence)).elements())
        errors.append(f"code blocks: {len(lost)} lost")

    o_bare = FENCE.sub("", orig)
    c_bare = FENCE.sub("", comp)

    o_url, c_url = set(URL.findall(o_bare)), set(URL.findall(c_bare))
    if o_url - c_url:
        errors.append(f"URLs lost: {sorted(o_url - c_url)}")

    o_in, c_in = Counter(INLINE.findall(o_bare)), Counter(INLINE.findall(c_bare))
    dropped = o_in - c_in
    if dropped:
        errors.append(f"inline code lost: {list(dropped.elements())}")

    o_path, c_path = set(PATH.findall(o_bare)), set(PATH.findall(c_bare))
    if o_path - c_path:
        warns.append(f"paths not present: {len(o_path - c_path)}")

    oh, ch = len(HEADING.findall(orig)), len(HEADING.findall(comp))
    if oh != ch:
        warns.append(f"heading count {oh} → {ch}")

    for w in warns:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")

    if errors:
        print("\n# unsafe — roll back to original")
        sys.exit(1)
    print(f"\n# ok — must-keeps preserved ({len(warns)} cosmetic warning(s))")


if __name__ == "__main__":
    main()
