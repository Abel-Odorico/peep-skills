# Mjolnir

**A Context Operating System for AI coding agents.**

Mjolnir loads the *right* context, not the *maximum* context. It is a discipline —
plus a small toolkit — for answering correctly while reading as little of a
codebase as possible. Every unnecessary token is cost, latency, and noise.

> The best context is not the largest. It is the smallest one that still
> guarantees the correct answer.

---

## Why

Coding agents waste tokens in predictable ways: they read whole files to see one
function, dump noisy build/test logs into the window, re-read files they already
saw, and keep expanding "just in case." On broad "understand the whole thing"
tasks this compounds fast.

Mjolnir replaces *read-everything* with *investigate-then-load*: map the repo
cheaply, rank what matters, pull signatures and single symbols instead of files,
filter tool output at the boundary, and stop the moment confidence is sufficient.

**Measured:** on a broad "map the whole system" task in a large repository, an
agent following Mjolnir used **~68% fewer tokens** and made **82% fewer
whole-file reads** than an unguided agent — reaching the same answer.

---

## Highlights

- **Zero dependencies.** Pure Python standard library. One folder, no install
  step, runs in any repository.
- **Progressive loading.** Four levels (structure → signatures → single method →
  whole file); never skip straight to full files.
- **Real AST for Python.** Exact symbols and imports via the `ast` module;
  robust regex + alias/relative resolution for other languages.
- **Structured output filtering.** Compresses test/build/lint/git output
  (failures-first, dedupe, per-tool parsers) with a full-output recovery file.
- **Safety by default.** Never loads credential files; never compresses away a
  failing line or security-relevant code; every lossy step is reversible.
- **Self-tested.** 60+ unit, golden, and CLI tests gate every change.

---

## Install

Mjolnir is a [Claude Code](https://claude.com/claude-code) skill. Place it where
your agent discovers skills:

```bash
git clone https://github.com/antoniocostalopes/mjolnir.git ~/.agents/skills/mjolnir
ln -s ~/.agents/skills/mjolnir ~/.claude/skills/mjolnir   # if your setup uses symlinked skills
```

The agent loads it automatically when a request matches its triggers (large or
unfamiliar repo, broad comprehension task, filling context window). The
`scripts/` tools are plain Python and can also be run directly:

```bash
python3 ~/.agents/skills/mjolnir/scripts/selftest.py   # verify the install
```

---

## How it works

### The pipeline

```
intent → plan → cheap discovery → score → expand one level → confidence check → stop or continue
```

Never skip straight to loading files. Plan first, discover cheaply, and climb
exactly one level of detail at a time.

### Investigate, don't search

For non-trivial "why / how / where" questions, Mjolnir behaves like a detective
rather than a grep loop:

```
observe → hypotheses → rank by confidence → gather evidence → drop weak → confirm root cause → load only what's needed → answer → stop
```

Read the repo's DNA first (stack + architecture → likely locations), pick the
search strategy that fits the intent, and check impact before changing a symbol.

### Progressive expansion (the core lever)

| Level | Load | Cost | Tool |
|-------|------|------|------|
| 0 | Repo structure: folders, packages, dependency graph | very low | `index.py`, `graph.py` |
| 1 | Public signatures: functions, classes, exports, imports | low | `symbols.py` |
| 2 | Only the specific method(s) needed | medium | `slice.py` |
| 3 | Whole file — only when unavoidable | high | full read |

If the current level cannot answer, expand **one** level and re-evaluate. Never
skip levels.

---

## Tools

All scripts are Python standard library only, respect a built-in ignore list
(`node_modules`, `vendor`, `dist`, lock files, binaries, media…), and refuse to
read credential files.

| Script | Purpose |
|--------|---------|
| `dna.py [path]` | Detect stack + architecture; name the likely locations to search first |
| `index.py [path]` | Level 0 map: folders, file counts, token estimates (from byte size) |
| `token_estimate.py [path] --top N` | Rank files by estimated token cost |
| `find.py <term> [path]` | Concept search — returns the enclosing symbol per hit, not raw grep lines |
| `graph.py [path]` | Import graph (AST-exact for Python): hubs, `--path a b`, `--cluster`, `--importers f`, `--orphans` |
| `symbols.py <file>...` | Signatures only, no bodies (AST for Python); cached by content hash |
| `slice.py <file> <name>` | Extract one function/class body by name — never read a whole file for one symbol |
| `score.py <path> "request" --target f --min N` | Rank candidates 0–100; auto-load ≥ 60 |
| `filter_output.py` (stdin) `--cmd "cmd"` | Compress tool output; structured parsers; anti-inflation guard; recovery tee |
| `verify.py <orig> <compressed>` | Prove a lossy pass kept URLs/code/inline tokens; exit 1 = roll back |
| `harvest.py [path]` | List `mjolnir: skipped …` deferral markers; flag those with no revisit trigger |
| `bench.py [path]` | Measure the real signatures-vs-full saving, with a distribution |
| `selftest.py` | Unit + golden + CLI tests; exit 1 on any failure |

### Examples

```bash
# 1. Understand a repo cheaply, before reading anything
python3 scripts/dna.py .            # stack + where to look
python3 scripts/index.py .          # folder map + token cost
python3 scripts/graph.py .          # dependency hubs (load these first)

# 2. Locate a concept as symbols, then read only that symbol
python3 scripts/find.py "authenticate" src/
python3 scripts/slice.py src/auth/service.ts login   # just the login() body

# 3. Rank candidate files for a task
python3 scripts/score.py . "fix login token validation" --target src/auth/login.ts

# 4. Filter a noisy command before it enters context
pytest 2>&1 | python3 scripts/filter_output.py --cmd "pytest"

# 5. Impact / dead-code
python3 scripts/graph.py . --importers src/auth/AuthService.ts   # blast radius
python3 scripts/graph.py . --orphans                            # dead-code candidates
```

---

## The doctrine (18 rules)

The full doctrine lives in [`SKILL.md`](SKILL.md). In brief:

1. **Plan before reading** — decide subsystem, entry points, and what to ignore first.
2. **Progressive expansion** — load in levels, never jump to full files.
3. **Context budget** — treat context as finite; stop expanding once confidence is enough.
4. **Context temperature** — evict cold context before warm, warm before hot.
5. **Reuse before reading** — conversation → summaries → signatures → fingerprints → file.
6. **File fingerprints** — a content hash means "already known, don't reload."
7. **Structural compression** — replace bulk code with its structure.
8. **Semantic deduplication** — load the canonical shape, reference variations.
9. **Smart ignore** — skip generated code, build output, locks, binaries.
10. **Output compression** — never inject noisy logs; keep failing lines.
11. **Confidence-driven expansion** — `<60` need more, `60–85` probably enough, `>90` stop.
12. **Auto-stop** — stop the moment the answer is confirmed.
13. **Search memory** — record dead ends; never revisit them.
14. **Learning** — track where answers were found; prioritize those next.
15. **Summaries instead of files** — reason from a summary before reopening.
16. **Safety floor** — never compress away failing/security/auth code; when unsure, include.
17. **Reversible compression** — every compressed form recovers the original.
18. **Token-efficiency priority** — when quality ties, pick the cheaper representation.

---

## Architecture

```
mjolnir/
├── SKILL.md                     # doctrine (18 rules) + investigation mode + tool index
├── README.md
├── references/
│   ├── frameworks.md            # where code lives + what to ignore, per stack
│   ├── heuristics.md            # scoring table, context levels, provenance tiers
│   ├── investigation.md         # hypotheses, evidence, DNA, intent templates, impact
│   └── measurement.md           # how to report savings honestly + measured results
└── scripts/                     # Python stdlib, zero dependencies
    ├── common.py                # ignore lists, secret guard, classifier, cache, AST, args
    ├── dna.py  index.py  token_estimate.py  graph.py  symbols.py
    ├── find.py  slice.py  score.py
    ├── filter_output.py  filters.json
    ├── verify.py  harvest.py  bench.py
    └── selftest.py
```

---

## Design guarantees

- **Secrets never enter context.** `.env`, private keys, `credentials*`,
  `.ssh`/`.aws` paths, and secret-token filenames are refused before load — no
  read, no summary, no hand-off to a sub-agent.
- **Reversible by construction.** Code, URLs, paths, identifiers, versions, and
  exact error strings are preserved verbatim. `filter_output.py` tees the full
  raw output to a recovery file; `verify.py` proves must-keeps survived a lossy
  pass and signals a rollback if not.
- **Never worse.** Compression that would grow the output is discarded in favor
  of the raw. Tools cap their own output so they can never flood the window.
- **Fail toward loading.** The dangerous failure of a context *reducer* is
  dropping something needed, so on any doubt it includes rather than excludes.
- **Deterministic + cached.** Repeatable passes are keyed by content hash with a
  size+mtime fast path and atomic writes; an unchanged file costs nothing on
  re-visit.

---

## Measured results

Numbers are estimates (~4 chars/token) and specific to the task, not universal —
see [`references/measurement.md`](references/measurement.md) for the honesty
rules and the full method (fresh agent, no skill vs. Mjolnir, same task).

| Task | Tokens (baseline → Mjolnir) | Whole-file reads |
|------|-----------------------------|------------------|
| Broad "map the whole system", large repo | 139.7k → 45.2k (**−68%**) | 11 → 2 |
| Multi-file trace, well-factored repo | 27.5k → 24.5k (**−11%**) | 0 → 0 |

Single-lever check: loading one symbol with `slice.py` instead of its file — e.g.
13 lines vs a 323-line file (**96%** less for that read).

The win is large on broad, comprehensive tasks where an unguided agent reads many
files whole; it shrinks on pinpoint lookups where a grep-first agent is already
efficient. The tools' consistent value is enforcing the floor — never read a
whole file for one symbol — deterministically rather than by luck.

---

## Testing

```bash
python3 scripts/selftest.py
```

Runs 60+ checks: the secret guard, file classifier, AST extraction, import
resolution (aliases + relative), the scoring ranker, single-symbol slicing,
concept search, structured output parsers, cache round-trips, and a golden table
for every `filters.json` entry. Exits non-zero on any failure.

---

## Philosophy

Most assistants search repositories; Mjolnir investigates them. Most assistants
load files; Mjolnir loads evidence. The objective is not to read more code — it
is to **understand more while reading less**.
