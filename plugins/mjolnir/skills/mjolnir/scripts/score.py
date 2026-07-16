#!/usr/bin/env python3
"""Rank candidate files for a request, so you auto-load only what scores >= 60.

Usage:
    python3 score.py <path> "<request text>" [--target <file>] [--min N]

Turns the relevance doctrine (SKILL.md / heuristics.md) into a number. Combines
cheap signals — feature/keyword overlap (rare terms weighted higher), entity
match against a file's symbols, and proven import edges to a --target — into a
0-100 score. Prints candidates sorted desc; >= --min (default 60) is the
auto-load set, the rest is "load only on a gap".

No git or network needed. Approximate by design — a ranking, not a verdict.
"""
import math
import os
import re
import sys
from collections import defaultdict
from common import walk_files, read_text, is_sensitive, parse_args
import graph as G
import symbols as S

SRC_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".php",
           ".go", ".rb", ".rs", ".java", ".vue", ".svelte"}
STOP = {"the", "and", "for", "with", "that", "this", "から", "add", "fix", "use",
        "get", "set", "new", "how", "why", "when", "where", "into", "from",
        "code", "file", "files", "please", "need", "want", "make", "should"}
ROUTE_HINT = re.compile(r"(/[\w:-]+|endpoint|route|api|http|get|post|put|delete)", re.I)


def terms_of(text):
    return [w for w in re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", text.lower())
            if w not in STOP]


def entities_of(text):
    # Capitalized words = likely model/type/entity names.
    return set(re.findall(r"\b[A-Z][a-zA-Z0-9]{2,}\b", text))


def main():
    pos, opts = parse_args(value_flags=("target", "min"))
    if len(pos) < 2:
        print(__doc__)
        sys.exit(2)
    root, request = pos[0], pos[1]
    target = os.path.abspath(opts["target"]) if opts.get("target") else None
    minimum = int(opts.get("min") or 60)

    q_terms = set(terms_of(request))
    q_entities = entities_of(request)
    is_route_q = bool(ROUTE_HINT.search(request))

    files = [p for p, _ in walk_files(root)
             if os.path.splitext(p)[1] in SRC_EXT and not is_sensitive(p)]

    # Document frequency per term → rarer term weighs more (IDF).
    df = defaultdict(int)
    file_terms = {}
    for p in files:
        toks = set(terms_of(p + " " + read_text(p)[:4000]))
        file_terms[p] = toks
        for t in toks & q_terms:
            df[t] += 1
    # Smoothed inverse document frequency: a term in few files weighs more than
    # one that appears everywhere. The +1 offsets keep it stable at df=0 and n=0.
    n = max(1, len(files))
    idf = {t: math.log((1 + n) / (1 + df.get(t, 0))) + 1 for t in q_terms}
    idf_max = max(idf.values()) if idf else 1.0

    # Proven import edges to the target (both directions count as strong).
    linked = set()
    if target:
        _, importers, out_edges = G.build(root)
        linked = set(importers.get(target, ())) | set(out_edges.get(target, ()))

    rows = []
    for p in files:
        if p == target:
            continue
        score = 0.0
        # Feature/keyword overlap. Score by absolute rare-term strength (each
        # rare hit is worth more), capped — not by fraction of all query terms,
        # which no single file ever contains.
        hit = q_terms & file_terms[p]
        if hit:
            strength = sum(idf[t] for t in hit) / (idf_max or 1)
            score += min(35, 13 * strength)
        # Entity: request names a type/model this file defines (cap 20).
        if q_entities:
            syms = " ".join(s for _, s in S.extract(p))
            if any(e in syms for e in q_entities):
                score += 20
        # Proven import edge to target (25).
        if p in linked:
            score += 25
        # Route request and file mentions a matching route token (10).
        if is_route_q and ROUTE_HINT.search(read_text(p)[:2000]):
            score += 10
        score = min(100, round(score))
        if score > 0:
            rows.append((score, p))

    rows.sort(reverse=True)
    keep = [r for r in rows if r[0] >= minimum]
    print(f"# Mjolnir relevance — {len(keep)} file(s) >= {minimum} (auto-load)\n")
    print(f"{'SCORE':>5}  FILE")
    for score, p in rows[:30]:
        mark = "  <- load" if score >= minimum else ""
        print(f"{score:>5}  {p}{mark}")


if __name__ == "__main__":
    main()
