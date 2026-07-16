#!/usr/bin/env python3
"""Measure Mjolnir's real token savings on a repo — honestly.

    python3 bench.py [path]

Reports the reduction of the core lever (loading signatures instead of whole
files) with a distribution, not a single number. This is a MEASURED figure for
THIS repo against a sane baseline (reading the files in full — the naive move
the lever replaces), not an invented per-session delta. Estimates use ~4
chars/token, so absolute numbers are approximate ('est.').

See references/measurement.md for the honesty rules this follows.
"""
import os
import statistics
from common import walk_files, estimate_from_size, estimate_tokens, parse_args
import symbols as S

SRC_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".php",
           ".go", ".rb", ".rs", ".java", ".vue", ".svelte"}


def main():
    pos, _ = parse_args()
    root = pos[0] if pos else "."
    files = [(p, sz) for p, sz in walk_files(root)
             if os.path.splitext(p)[1] in SRC_EXT]
    if not files:
        print("# no source files to benchmark")
        return

    full_total = sym_total = 0
    reductions = []
    for p, sz in files:
        full = estimate_from_size(sz)
        rendered = "\n".join(s for _, s in S.extract(p))
        sym = estimate_tokens(rendered) if rendered else 1
        full_total += full
        sym_total += sym
        if full >= 50:                    # ignore trivially small files
            reductions.append(1 - sym / full)

    overall = 0 if full_total == 0 else round((1 - sym_total / full_total) * 100)
    print(f"# Mjolnir benchmark — {root}")
    print(f"# {len(files)} source files. Lever: signatures instead of full files.\n")
    print(f"  full corpus      ~{full_total:,} tok (est.)")
    print(f"  signatures only  ~{sym_total:,} tok (est.)")
    print(f"  overall reduction {overall}%")
    if reductions:
        pct = [round(r * 100) for r in reductions]
        print(f"\n  per-file reduction over {len(pct)} non-trivial files (est.):")
        print(f"    median {statistics.median(pct)}%   mean {round(statistics.mean(pct))}%"
              f"   min {min(pct)}%   max {max(pct)}%")
        if len(pct) > 1:
            print(f"    stdev {round(statistics.pstdev(pct))}%  "
                  f"(spread shows how solid the number is)")
    print("\n# Honest scope: measured on THIS repo vs reading files in full. "
          "Savings scale with file size — small files gain little. Not a claim "
          "about a session you didn't run.")


if __name__ == "__main__":
    main()
