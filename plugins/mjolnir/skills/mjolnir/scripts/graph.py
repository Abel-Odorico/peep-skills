#!/usr/bin/env python3
"""Map the repo's dependency structure so you load the highest-signal files.

Usage:
    python3 graph.py [path] [--top N]              # rank files by import in-degree
    python3 graph.py [path] --importers <file>     # who imports this file
    python3 graph.py [path] --path <a> <b>         # shortest import path a→b
    python3 graph.py [path] --cluster              # group files into subsystems

Builds a lightweight import/reference graph from source. High in-degree = a hub
that explains the most per token — load it first. Path and cluster views turn
"what depends on what" into a discovery primitive so you fetch a coherent slice
(one subsystem, one dependency chain) instead of scattered files.

Language-agnostic: reads import/require/use/from statements, resolves by module
basename. Approximate by design — a cheap map, not a compiler.
"""
import json
import os
import re
from collections import defaultdict, deque
from common import walk_files, read_text, GENERIC_SYMBOLS, parse_args, py_imports

SRC_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".php",
           ".go", ".rb", ".rs", ".java", ".vue", ".svelte"}

# import/export … from '…', require('…'), python from/import, php/rust use.
IMPORT_RX = [
    re.compile(r"""(?:import|export)\s+.*?from\s+['"]([^'"]+)['"]""", re.S),
    re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
    re.compile(r"""^\s*from\s+([\w.]+)\s+import""", re.M),
    re.compile(r"""^\s*import\s+([\w.]+)""", re.M),
    re.compile(r"""^\s*use\s+([\w\\]+)""", re.M),
]


def module_token(spec):
    spec = spec.replace("\\", "/").replace(".", "/")
    return os.path.basename(spec.rstrip("/")).lower()


def load_aliases(root):
    """Read tsconfig/jsconfig path aliases (@/lib → src/lib) so aliased imports
    resolve to real files instead of dropping to a basename guess."""
    aliases = {}
    for cfg in ("tsconfig.json", "jsconfig.json"):
        text = read_text(os.path.join(root, cfg))
        if not text:
            continue
        text = re.sub(r"//.*", "", text)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        try:
            opts = json.loads(text).get("compilerOptions", {})
        except ValueError:
            continue
        base = opts.get("baseUrl", ".")
        for key, targets in (opts.get("paths") or {}).items():
            if targets:
                prefix = key.replace("*", "")
                dest = targets[0].replace("*", "")
                aliases[prefix] = os.path.normpath(os.path.join(root, base, dest))
    return aliases


def build(root):
    """Return (files, importers, out_edges).
    importers: file -> set of files that import it (in-edges).
    out_edges: file -> set of files it imports (out-edges).

    Relative and aliased specs resolve to the actual file (extension/index
    inferred); bare module names fall back to a unique basename match."""
    files = [p for p, _ in walk_files(root)
             if os.path.splitext(p)[1] in SRC_EXT]
    abspaths = {os.path.abspath(p): p for p in files}
    by_noext = {os.path.splitext(os.path.abspath(p))[0]: p for p in files}
    by_stem = defaultdict(list)
    for p in files:
        stem = os.path.splitext(os.path.basename(p))[0].lower()
        if stem not in GENERIC_SYMBOLS:
            by_stem[stem].append(p)
    aliases = load_aliases(root)

    def match_path(cand):
        cand = os.path.normpath(cand)
        if cand in abspaths:
            return [abspaths[cand]]
        if cand in by_noext:
            return [by_noext[cand]]
        for ext in SRC_EXT:
            if cand + ext in abspaths:
                return [abspaths[cand + ext]]
        for ext in SRC_EXT:                       # barrel: dir/index.*
            idx = os.path.join(cand, "index" + ext)
            if idx in abspaths:
                return [abspaths[idx]]
        return []

    def resolve(importer, spec):
        for prefix, dest in aliases.items():
            if prefix and spec.startswith(prefix):
                hit = match_path(os.path.join(dest, spec[len(prefix):]))
                if hit:
                    return hit
        if spec.startswith("."):
            base = os.path.dirname(os.path.abspath(importer))
            return match_path(os.path.join(base, spec))
        tok = module_token(spec)
        if not tok or tok in GENERIC_SYMBOLS:
            return []
        return by_stem.get(tok, [])

    def specs_of(p):
        # Python: exact module names via AST (no string/comment false hits).
        if p.endswith(".py"):
            mods = py_imports(p)
            if mods is not None:
                return mods
        text = read_text(p)
        found = []
        for rx in IMPORT_RX:
            found.extend(rx.findall(text))
        return found

    importers = defaultdict(set)
    out_edges = defaultdict(set)
    for p in files:
        seen = set()
        for spec in specs_of(p):
            if spec in seen:
                continue
            seen.add(spec)
            for target in resolve(p, spec):
                if target != p:
                    importers[target].add(p)
                    out_edges[p].add(target)
    return files, importers, out_edges


def undirected(files, out_edges):
    adj = defaultdict(set)
    for a in files:
        for b in out_edges.get(a, ()):
            adj[a].add(b)
            adj[b].add(a)
    return adj


def resolve(files, needle):
    """Best file match for a bare name or path fragment."""
    needle = needle.lower()
    exact = [f for f in files
             if os.path.splitext(os.path.basename(f))[0].lower() == needle]
    if exact:
        return min(exact, key=len)
    partial = [f for f in files if needle in f.lower()]
    return min(partial, key=len) if partial else None


def cmd_path(files, out_edges, a, b):
    src, dst = resolve(files, a), resolve(files, b)
    if not src or not dst:
        print(f"# no match for {a if not src else b}")
        return
    adj = undirected(files, out_edges)
    # BFS shortest path — undirected so query order does not matter.
    prev, q = {src: None}, deque([src])
    while q:
        cur = q.popleft()
        if cur == dst:
            break
        for nb in sorted(adj.get(cur, ())):
            if nb not in prev:
                prev[nb] = cur
                q.append(nb)
    if dst not in prev:
        print(f"# no import path between {os.path.basename(src)} and {os.path.basename(dst)}")
        return
    chain, cur = [], dst
    while cur is not None:
        chain.append(cur)
        cur = prev[cur]
    print(f"# import path ({len(chain) - 1} hops):")
    for f in reversed(chain):
        print(f"  {f}")


def cmd_cluster(files, importers, out_edges):
    adj = undirected(files, out_edges)
    seen, groups = set(), []
    for f in sorted(files):
        if f in seen or f not in adj:
            continue
        comp, q = [], deque([f])
        seen.add(f)
        while q:
            cur = q.popleft()
            comp.append(cur)
            for nb in sorted(adj.get(cur, ())):
                if nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        groups.append(comp)
    # Label each subsystem by its highest in-degree member (deterministic).
    groups.sort(key=lambda g: (-len(g), min(g)))
    print(f"# {len(groups)} connected subsystem(s):\n")
    for comp in groups:
        hub = max(sorted(comp), key=lambda f: len(importers.get(f, ())))
        label = os.path.splitext(os.path.basename(hub))[0]
        print(f"[{label}]  {len(comp)} files")
        for f in sorted(comp)[:8]:            # cap: a map, not a full dump
            print(f"    {f}")
        if len(comp) > 8:
            print(f"    … +{len(comp) - 8} more (hub: {hub})")


def main():
    pos, opts = parse_args(value_flags=("top", "importers"))
    root = pos[0] if pos else "."
    files, importers, out_edges = build(root)

    if "path" in opts:
        if len(pos) < 3:
            print("# usage: graph.py <path> --path <a> <b>")
            return
        cmd_path(files, out_edges, pos[1], pos[2])
        return
    if "cluster" in opts:
        cmd_cluster(files, importers, out_edges)
        return
    if "orphans" in opts:
        # In-degree 0 = nothing imports it. Entry points legitimately have 0,
        # so flag them separately rather than calling them dead.
        entry = ("index", "main", "app", "server", "cli", "__main__",
                 "setup", "conftest")
        dead, entries = [], []
        for f in sorted(files):
            if importers.get(f):
                continue
            stem = os.path.splitext(os.path.basename(f))[0].lower()
            (entries if stem in entry else dead).append(f)
        print(f"# {len(dead)} orphan candidate(s) — imported by nothing "
              f"(dead-code candidates; verify before removing):")
        for f in dead[:40]:
            print(f"  {f}")
        if len(dead) > 40:
            print(f"  … +{len(dead) - 40} more")
        if entries:
            print(f"\n# {len(entries)} entry-point(s) (0 imports is expected):")
            for f in entries:
                print(f"  {f}")
        return
    if opts.get("importers"):
        target = os.path.abspath(opts["importers"])
        who = sorted(importers.get(target, []))
        print(f"# {len(who)} files import {target}")
        for w in who[:40]:
            print(f"  {w}")
        if len(who) > 40:
            print(f"  … +{len(who) - 40} more")
        return

    top = int(opts.get("top") or 20)
    ranked = sorted(files, key=lambda f: len(importers.get(f, ())), reverse=True)
    print(f"# Mjolnir dependency hubs — {root}")
    print(f"# {len(files)} source files. Load high in-degree first.\n")
    print(f"{'IN':>4}  FILE")
    for f in ranked[:top]:
        deg = len(importers.get(f, ()))
        if deg == 0:
            continue
        print(f"{deg:>4}  {f}")


if __name__ == "__main__":
    main()
