#!/usr/bin/env python3
"""Extract signatures/symbols from a file instead of loading the whole thing.

Usage:
    python3 symbols.py <file> [file2 ...]

Prints classes, functions, interfaces, types, exports, hooks, constants —
the shape of the code without the bodies. Often 80-95% fewer tokens than the
full file, enough to reason about the interface (Context Level 2-4).
"""
import re
import sys
from common import read_text, cache_get, cache_set, py_symbols

# Language-agnostic signature patterns. Match the declaration line, drop bodies.
PATTERNS = [
    r"^\s*(export\s+)?(default\s+)?(async\s+)?function\s+\w+.*",
    r"^\s*(export\s+)?(abstract\s+)?class\s+\w+.*",
    r"^\s*(export\s+)?interface\s+\w+.*",
    r"^\s*(export\s+)?type\s+\w+\s*=.*",
    r"^\s*(export\s+)?enum\s+\w+.*",
    r"^\s*(export\s+)?const\s+\w+\s*=\s*(async\s*)?\(.*",     # arrow fns
    r"^\s*(export\s+)?const\s+[A-Z_][A-Z0-9_]*\s*=.*",       # CONSTANTS
    r"^\s*(public|private|protected|static|def)\s+\w+.*",     # methods / python
    r"^\s*def\s+\w+.*",                                       # python funcs
    r"^\s*(pub\s+)?(fn|struct|trait|impl|enum)\s+\w+.*",      # rust
    r"^\s*func\s+\w+.*",                                      # go
    r"^\s*(public|private|protected)\s+(static\s+)?\w+.*\(.*",# php/java methods
]
COMPILED = [re.compile(p) for p in PATTERNS]


def extract(path):
    cached = cache_get(path, "symbols")
    if cached is not None:
        return [(int(n), s) for n, s in cached]
    # Python: exact via AST. Everything else / a parse failure: regex fallback.
    out = None
    if path.endswith(".py"):
        out = py_symbols(path)
    if out is None:
        out = []
        for i, line in enumerate(read_text(path).splitlines(), 1):
            s = line.strip()
            if not s or s.startswith(("//", "#", "*", "/*")):
                continue
            for rx in COMPILED:
                if rx.match(line):
                    out.append((i, re.sub(r"\s*\{\s*$", "", line.rstrip()).rstrip()))
                    break
    cache_set(path, "symbols", out)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for path in sys.argv[1:]:
        syms = extract(path)
        print(f"\n# {path}  ({len(syms)} symbols)")
        for lineno, sig in syms:
            print(f"{lineno:>5}: {sig}")


if __name__ == "__main__":
    main()
