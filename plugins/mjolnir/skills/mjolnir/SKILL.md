---
name: mjolnir
description: Use when gathering context in a large or unfamiliar codebase before answering, coding, or planning — especially on broad "understand/map/audit" tasks where the naive move is to read many files in full, when the context window is filling, or when token cost/latency matters. Loads the minimum right context instead of the maximum, and stops as soon as confidence is sufficient.
---

# Mjolnir — Context Operating System

**Load the right context, not the maximum context.** Every unnecessary token is
cost, latency, and noise. The goal: answer correctly using the least context
that still guarantees the correct answer. Mjolnir is not a search tool — it is a
discipline for spending the context budget.

## When to Use

Highest payoff on **broad, "be comprehensive" tasks** — map a subsystem,
understand how X works across the codebase, audit everything of a kind — where
the naive move is to read many files in full. (Measured: ~68% fewer tokens and
82% fewer whole-file reads than an unguided agent on that kind of task.)

**Skip for:** a pinpoint lookup ("where is constant X") — a grep-first agent is
already disciplined there. Also tiny repos and an explicit "read it all".

## The Pipeline (never skip straight to loading files)

```
intent → plan → cheap discovery → score → expand one level → confidence check → stop or continue
```

## Investigate, don't search

For non-trivial "why/how/where" tasks, don't grep-and-read — **investigate**.
Form hypotheses, rank them by confidence, gather evidence, open only the most
promising code. Load evidence, not files.

```
observe → hypotheses → rank → gather evidence → drop weak → confirm root cause → load only what's needed → answer → stop
```

Read the repo's DNA first (`dna.py`: stack + architecture → where to look), pick
the search strategy that fits the intent, and check impact before changing a
symbol (`graph.py --importers` = its callers = mandatory context). Full doctrine
in `references/investigation.md`.

## The Rules

**1 — Plan before reading.** Never open files first. Decide: what's asked, which
subsystem, probable entry points, likely dependencies, expected output. Name
what to ignore (tests, docs, unrelated features) before loading anything.

**2 — Progressive expansion.** Load in levels, never jump to full files:

| Level | Load | Cost | Tool |
|---|---|---|---|
| 0 | Repo structure: folders, packages, dependency graph | very low | `index.py`, `graph.py` |
| 1 | Public signatures only: functions, classes, exports, imports | low | `symbols.py` |
| 2 | Only the specific method(s) needed | medium | `slice.py` |
| 3 | Whole file — only when unavoidable | high | full read |

Need the answer? If no, expand **one** level, re-evaluate, repeat. Never skip levels.

**3 — Context budget.** Treat context as finite. Track spent vs remaining. Near
budget: replace old files with summaries, drop cold context, stop expanding once
confidence is enough. `token_estimate.py` / `bench.py` size the cost.

**4 — Context temperature.** Hot (recently used) → keep. Warm (referenced
recently) → compress if needed. Cold (unused for several steps) → summarize or
evict. Evict cold before warm, warm before hot. Never evict hot first.

**5 — Reuse before reading.** Search in order: current conversation → cached
summaries → cached signatures → fingerprints → original file. Reuse before
reopening.

**6 — File fingerprints.** Every analyzed file yields path, symbols, imports,
exports, responsibilities, and a content hash. If the fingerprint matches a prior
analysis, do not reload — reuse the knowledge. (`symbols.py` caches by content
hash with a size+mtime fast path.)

**7 — Structural compression.** Replace bulk code with structure: module →
classes → methods → dependencies → responsibilities. Expand only the required
method. 600 lines become a map plus one function.

**8 — Semantic deduplication.** A repo carries equivalent shapes (`User`,
`UserModel`, `UserDTO`, `UserResponse`…). Load the canonical one, reference the
rest — never every variation.

**9 — Smart ignore.** Skip unless explicitly asked: `node_modules`, `dist`,
`build`, `coverage`, `.next`, `.cache`, `tmp`, `vendor`, generated code
(OpenAPI/Prisma/GraphQL/protobuf/SDKs), lock files, `*.map`, `*.min.*`, media,
binaries. Enforced by `common.py`'s ignore lists.

**10 — Output compression.** Never inject noisy output (passing test logs, build
chatter, verbose traces, compiler progress). Give summary → errors → relevant
excerpts, original available. Always preserve failing lines. Pipe through
`filter_output.py` (failures-first, dedupe, per-tool structured parsers, recovery
tee).

**11 — Confidence-driven expansion.** After each expansion, estimate confidence.
`<60` need more context · `60–85` probably enough · `>90` stop. Never keep
reading "just in case". `score.py` ranks candidates 0–100.

**12 — Auto-stop.** Stop the moment the answer is located / definition confirmed /
references confirmed / imports confirmed / requested change understood. Reading
further after confidence wastes tokens.

**13 — Search memory.** Record dead ends ("checked `payments/` — no auth code").
Never search the same dead end twice.

**14 — Learning (this session).** Track where answers were found ("auth questions
→ resolved in `auth/`, `middleware/`, `session/`") and prioritize those next.
Applies to the current session unless explicitly persisted.

**15 — Summaries instead of files.** After reading a file whole, record purpose,
responsibilities, public API, dependencies, key constants, side effects, risks.
Future reasoning uses the summary before reopening.

**16 — Safety floor (never compress away).** Failing stack lines,
security/auth/authorization/encryption code, explicitly-requested secrets or
snippets. When uncertain, **include rather than exclude**. Separately: never load
credential files at all (`.env`, keys, `credentials*`, `.ssh`/`.aws`) — refused
before load.

**17 — Reversible compression.** Every compressed form must recover the original
file / lines / method / output. Compression never destroys recoverability
(`filter_output.py` tees raw; `verify.py` proves must-keeps survived).

**18 — Token-efficiency priority.** When strategies tie on reasoning quality,
pick the cheaper: summary → signature → method → section → whole file.

## Tools (`scripts/` — Python stdlib, zero deps)

| Script | Does |
|---|---|
| `dna.py [path]` | Detects stack + architecture → the likely locations to search first |
| `index.py [path]` | Level 0 map: folders, file counts, token estimates (from byte size) |
| `token_estimate.py [path] --top N` | Files ranked by estimated token cost |
| `find.py <term> [path]` | Concept search: returns the enclosing symbol per hit, not raw grep lines |
| `graph.py [path]` | Import graph (AST-exact for Python): hubs by in-degree; `--path a b`, `--cluster`, `--importers f` (impact), `--orphans` (dead-code candidates) |
| `symbols.py <file>...` | Signatures only, no bodies (AST for Python); cached by content hash |
| `slice.py <file> <name>` | Extracts one function/class body by name (Level 2) — never read a whole file for one symbol |
| `score.py <path> "request" --target f --min N` | Ranks candidates 0–100; auto-load ≥ 60 |
| `filter_output.py` (stdin) `--cmd "cmd"` | Compresses tool output; structured parsers (tsc, tests); anti-inflation guard; recovery tee |
| `verify.py <orig> <compressed>` | Proves a lossy pass kept URLs/code/inline tokens; exit 1 = roll back |
| `harvest.py [path]` | Lists `mjolnir: skipped …` deferral markers; flags those with no revisit trigger |
| `bench.py [path]` | Measures real signatures-vs-full saving with a distribution (labeled est.) |
| `selftest.py` | Unit + golden + CLI tests; exit 1 on any failure |

## References (load on demand)

- `references/frameworks.md` — where code lives + what to ignore per stack.
- `references/heuristics.md` — full scoring table, provenance tiers, dependency
  structure, compression order.
- `references/measurement.md` — reporting savings honestly (never invent a delta
  against a version you never loaded).
- `references/investigation.md` — investigate-don't-search doctrine: hypotheses,
  evidence, root cause, project DNA, intent templates, impact, adaptive strategy.

## Golden Rules

**Always:** plan first · load progressively · reuse existing context · compress
aggressively · cache summaries · stop early · measure confidence · respect the
budget.

**Never:** dump whole repositories · reload unchanged files · read generated code
needlessly · keep cold context forever · expand after confidence is sufficient ·
spend tokens on redundant information.

## Mission

Maximize reasoning quality while minimizing token consumption. The best context
is not the largest — it is the smallest one that still guarantees the correct
answer.
