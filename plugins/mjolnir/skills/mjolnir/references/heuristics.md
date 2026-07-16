# Mjolnir Heuristics — scoring, levels, compression detail

Load only when you need the full rules; SKILL.md has the summary.

## Relevance score (0–100)

| Factor | Weight | Meaning |
|---|---|---|
| Same feature | 30 | Same domain/module as the request |
| Direct import | 25 | Target file imports/requires it |
| Same entity | 20 | Operates on the same model/table/type |
| Same route | 10 | Same URL/endpoint/page |
| Git proximity | 10 | Recently changed together (co-commit) |
| Semantic similarity | 5 | Name/keyword overlap with the request |

- **≥ 60** auto-load. **40–59** load only if a gap appears. **< 40** skip.
- Dependency traversal: **direct deps only, max depth 5**. Do not follow
  transitive deps unless a specific one is named.
- **Rare-term weighting:** a match on a distinctive identifier is worth more
  than one on a generic word (`error`, `handler`, `index`). Weight a term by
  its rarity, and scale a candidate's score by how many of the query's terms it
  covers — one generic collision shouldn't outrank a real multi-term match.

## Dependency structure (via `graph.py`)

- **Hub (in-degree):** imported by many files — explains the most per token,
  load first. Filter language builtins/generics before ranking (a `String` or
  `index` node is noise, not a hub).
- **Bridge:** the file everything *routes through* between subsystems — distinct
  from a hub. High-value for "how does A reach B" questions.
- **Subsystem (`--cluster`):** a connected group; load the whole coherent slice
  ("the auth subsystem") instead of scattered files. Labeled by its hub member.
- **Dependency chain (`--path a b`):** the import path from one file to another —
  load exactly the chain the change flows along.
- **Impact (`--importers f`):** every file that depends on `f` — the blast radius
  to check before changing it.
- **Orphans (`--orphans`):** files imported by nothing (not entry points) —
  dead-code candidates that should stay out of context.

## Locating a concept

`find.py <term>` returns each match as its **enclosing symbol** (function/class),
not raw grep lines — so a concept reads as a handful of symbols. Then pull just
that symbol's body with `slice.py <file> <name>` instead of opening the file.

## Provenance tiers

Tag every loaded file by *why* it's here; trim low-confidence first.

| Tier | Criterion | Trust |
|---|---|---|
| Strong | Explicit import/call edge, or appears in the actual stack | Load; safe to rely on |
| Weak | Name/keyword match only, no proven edge | Load last; confirm the link before relying |
| Uncertain | Guessed relation | Keep visible, flag — do **not** silently drop |

Confirm a weak edge (`graph.py --importers`) before treating it as strong.

## Honest measurement

See `measurement.md` — never report a per-session savings delta against a
maximal-context version you never loaded; count what you actually skipped.

## Context Levels (Rule 2)

| Level | Load | Cost | Tool | Use when |
|---|---|---|---|---|
| 0 | Repo structure: folders, packages, dependency graph | very low | `index.py`, `graph.py` | Always first in a new/large repo |
| 1 | Public signatures: functions, classes, exports, imports | low | `symbols.py` | Reason about the interface/contract |
| 2 | The specific method(s) needed | medium | `slice.py` | Need a particular function's body/logic |
| 3 | Whole file | high | full read | Only when nothing above is enough |

Need the answer? If no, expand **one** level, re-evaluate, repeat. Never skip levels.

Start at 0. Climb one level only when the current level cannot answer.

## Compression order (apply until under budget)

1. Replace file with a 1–3 line summary
2. Extract symbols/signatures (`symbols.py`) instead of full file
3. Strip comments
4. Strip debug logs / console output
5. Remove duplicated context already in the window
6. Replace function bodies with signatures
7. Drop files scoring < 60

**Budget targets:** ≥50% reduction minimum, 75% preferred, 90%+ excellent.
Still over budget after all seven? Ask for the ONE missing piece — never
fabricate to fill the gap.

## Self-check gate (before acting)

- Do I need every loaded file?
- Can a summary replace this file?
- Can I load symbols instead of the file?
- Am I over budget?
- Is any context duplicated?
- Can I postpone loading anything?

Proceed only when all answers are optimized.
