#!/usr/bin/env python3
"""Shrink noisy command output BEFORE it reaches the context window.

Usage:
    <command> 2>&1 | python3 filter_output.py [--cmd "<command>"] [--width N] [--keep-pass]

Reads stdin (test/build/lint/install logs), emits a compact digest:
  - strips ANSI colour, spinners, progress bars, "Compiling…"-style chatter
  - collapses near-identical lines (timestamps/UUIDs/hashes masked) into one
    line + an (xN) count
  - surfaces error/failure lines first; drops passing noise unless --keep-pass
  - success-collapse: an all-passing run becomes a single line
  - truncates over-long lines to --width (default 200)
  - anti-inflation guard: if the digest is somehow bigger than the raw, emits raw
  - writes the FULL raw output to a recovery file and prints its path, so
    aggressive compression stays reversible — nothing is ever lost for good.

Pass --cmd to apply a named per-tool filter from filters.json (a declarative
registry); unknown commands fall through to the generic filter above.
"""
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from common import normalize_line, estimate_tokens, parse_args

ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
NOISE = re.compile(
    r"^\s*("
    r"[\-\\|/]\s*$"
    r"|\d+%|\[=*>?\s*\]"
    r"|Compiling |Building |Downloading |Fetching |Resolving "
    r"|info |verbose |debug )",
    re.I,
)
FAIL = re.compile(r"(error|fail|failed|exception|panic|traceback|✗|✖|✘|"
                  r"cannot |unable to |not found|undefined)", re.I)
PASS = re.compile(r"(\bpass(ed)?\b|✓|✔|\bok\b|\bsuccess\b|\bdone\b)", re.I)

HERE = os.path.dirname(os.path.abspath(__file__))


def clean(line):
    return ANSI.sub("", line.rstrip("\n")).rstrip()


def load_registry():
    try:
        with open(os.path.join(HERE, "filters.json"), encoding="utf-8") as f:
            return json.load(f).get("filters", {})
    except (OSError, ValueError):
        return {}


def apply_registry(raw, command):
    """Apply the first filter whose 'match' regex hits the command. Returns
    (text, None) on no match so the caller falls back to the generic filter."""
    for name, spec in load_registry().items():
        if re.search(spec.get("command", r"$^"), command):
            # success short-circuit, guarded so it never swallows a real error
            for rule in spec.get("shortcut", []):
                if re.search(rule["if"], raw) and not (
                        rule.get("skip_if") and re.search(rule["skip_if"], raw)):
                    return rule["emit"], name
            lines = raw.splitlines()
            for pat in spec.get("strip", []):
                rx = re.compile(pat)
                lines = [ln for ln in lines if not rx.search(ln)]
            only = spec.get("only")
            if only:
                rx = re.compile("|".join(only))
                lines = [ln for ln in lines if rx.search(ln)]
            cap = spec.get("cap")
            if cap and len(lines) > cap:
                lines = lines[:cap] + [f"… +{len(lines) - cap} more (see recovery file)"]
            return "\n".join(lines), name
    return None, None


_TSC = re.compile(r"^(.*?)\((\d+),\d+\):\s*error\s+(TS\d+):\s*(.*)$")


def parse_tsc(raw):
    """Cluster tsc errors by file and count by error code — the shape you need,
    not the wall of lines."""
    by_file, codes = defaultdict(list), Counter()
    for line in raw.splitlines():
        m = _TSC.match(line.strip())
        if m:
            by_file[m.group(1)].append((m.group(2), m.group(3), m.group(4)))
            codes[m.group(3)] += 1
    if not by_file:
        return None
    total = sum(len(v) for v in by_file.values())
    out = [f"# tsc: {total} error(s) in {len(by_file)} file(s)",
           "# top codes: " + ", ".join(f"{c} (x{n})" for c, n in codes.most_common(5))]
    for f in sorted(by_file, key=lambda k: -len(by_file[k])):
        rows = by_file[f]
        out.append(f"{f}: {len(rows)} error(s)")
        for ln, code, msg in rows[:3]:
            out.append(f"  L{ln} {code}: {msg[:100]}")
        if len(rows) > 3:
            out.append(f"  … +{len(rows) - 3} more")
    return "\n".join(out)


def parse_tests(raw):
    """Keep only failure lines and the summary; drop the passing majority."""
    fails, summary = [], None
    for line in raw.splitlines():
        s = line.strip()
        if re.search(r"\b(FAIL(ED)?|✕|✗)\b|^E\s|AssertionError", s):
            fails.append(s)
        if re.search(r"\b\d+ (passed|failed)\b|test result:|Tests:\s", s):
            summary = s
    if not fails and not summary:
        return None
    out = []
    if fails:
        out.append(f"# {len(fails)} failure line(s):")
        out.extend(fails[:15])
        if len(fails) > 15:
            out.append(f"… +{len(fails) - 15} more")
    if summary:
        out.append(summary)
    return "\n".join(out)


def structured(raw, command):
    """Deep per-tool parsers — richer than the declarative registry."""
    if re.search(r"\btsc\b|type-?check", command, re.I):
        return parse_tsc(raw)
    if re.search(r"\b(pytest|jest|vitest|go\s+test|cargo\s+test)\b", command, re.I):
        return parse_tests(raw)
    return None


def generic(raw, width, keep_pass):
    fails, kept = [], []
    prev_norm, prev_raw, count = None, None, 0

    def flush():
        if prev_raw is None:
            return
        line = prev_raw if count == 1 else f"{prev_raw}  (x{count})"
        (fails if FAIL.search(prev_raw) else kept).append(line)

    saw_pass = False
    for line in raw.splitlines():
        c = clean(line)
        if not c or NOISE.match(c):
            continue
        if not keep_pass and PASS.search(c) and not FAIL.search(c):
            saw_pass = True
            continue
        if len(c) > width:
            c = c[:width] + " …"
        norm = normalize_line(c)
        if norm == prev_norm:
            count += 1
        else:
            flush()
            prev_norm, prev_raw, count = norm, c, 1
    flush()

    # Success-collapse: nothing failed and everything else was passing noise.
    if not fails and not kept and saw_pass:
        return "ok — all checks passed"

    out = []
    if fails:
        out.append(f"# {len(fails)} problem line(s):")
        out.extend(fails)
    if kept:
        if fails:
            out.append("")
        out.extend(kept)
    return "\n".join(out)


def main():
    _, opts = parse_args(value_flags=("width", "cmd"))
    keep_pass = "keep-pass" in opts
    width = int(opts.get("width") or 200)
    command = opts.get("cmd") or ""

    raw = sys.stdin.read()
    fd, recovery = tempfile.mkstemp(prefix="mjolnir_out_", suffix=".log")
    with os.fdopen(fd, "w", encoding="utf-8", errors="ignore") as f:
        f.write(raw)

    digest, used = (None, None)
    if command:
        deep = structured(raw, command)
        if deep is not None:
            digest, used = deep, "structured"
        else:
            digest, used = apply_registry(raw, command)
    if digest is None:
        digest = generic(raw, width, keep_pass)

    # Anti-inflation guard: compression must never make it bigger. Fall to raw.
    if estimate_tokens(digest) > estimate_tokens(raw):
        digest = raw.rstrip()
        used = "raw (compression would have grown it)"

    print(digest)
    tag = f" via {used}" if used else ""
    before, after = len(raw), len(digest)
    pct = 0 if before == 0 else round((1 - after / before) * 100)
    print(f"\n# mjolnir{tag}: {before:,} → {after:,} chars ({pct}% smaller). "
          f"Full output: {recovery}")


if __name__ == "__main__":
    main()
