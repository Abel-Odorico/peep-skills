# Measuring savings honestly

Load when reporting how many tokens Mjolnir saved. A token-optimizer that
inflates its own numbers is worse than none — it hides the cases where it hurt.

## The cardinal rule: never invent the counterfactual

You **cannot** claim "saved X tokens" on a live task, because the maximal-context
version was never loaded — there is no real baseline to subtract from. Reporting
`load_everything − what_I_loaded` is guessing savings into existence.

Report only:
- **Counted, real figures:** files actually skipped, symbols loaded instead of
  bodies, chars dropped by `filter_output.py` (it prints a measured before/after
  on real input).
- **Benchmark medians** from a controlled run, clearly labeled "measured, not
  computed from this repo."

Never a per-session delta against a version you didn't run.

## Baseline: compare to reasonable, not to worst-case

Measuring against "load the entire repo" over-credits you — nobody would do
that. Compare against a **naive-but-sane baseline**: e.g. "load every file whose
name matches the query." Savings = how much better selection does than that.

## Account for your own overhead

Mjolnir isn't free: its own instructions, the index read, and cache lookups all
cost input tokens. A honest number is *net* of that overhead. On tiny repos or
already-terse tasks the overhead can exceed the savings — say so.

## State which token class you reduce

Mjolnir reduces **input/context** tokens. Don't label that as "usage" or "budget"
savings if input+cache dominate and are untouched. Be specific: "context tokens
loaded," not "tokens."

## Report the distribution, flag the estimate

- Show median, min, max — not just a mean — so a reader sees whether a number is
  solid or noisy.
- Token counts from a char/4 heuristic (or a non-matching tokenizer) are
  **approximate** — label them `est.`.
- Savings scale with corpus size. On a 6-file repo the value is structural
  clarity, not compression — don't quote a big multiplier there.

## Measured results (RED-GREEN, method above)

Each run: the same task given to a fresh agent with no skill (RED) and one
following Mjolnir (GREEN); compare tokens, tool calls, and whole-file reads.
Numbers are `est.` and specific to the task — not universal.

| Task type | Tokens (RED → GREEN) | Whole-file reads | Verdict |
|---|---|---|---|
| Broad "map the whole system" (large repo) | 139.7k → 45.2k (**−68%**) | 11 → 2 | Big win — the naive agent over-reads |
| Multi-file trace, well-factored repo | 27.5k → 24.5k (**−11%**) | 0 → 0 | Modest — a grep-first baseline is already disciplined |

Single-lever check (`bench.py`): loading one symbol via `slice.py` instead of
its whole file — e.g. `is_sensitive` = 13 lines vs a 323-line file (**96%** less
for that read). This is a counted, real figure, not a counterfactual.

**Honest reading:** the win is large on broad/comprehensive tasks where an
unguided agent reads many files whole; it shrinks to single digits on pinpoint
lookups where grep-first agents are already efficient. The tools' consistent
value is enforcing the floor (never read a whole file for one symbol) — the
baseline may reach it by luck; Mjolnir makes it deterministic.

## When a technique doesn't help

- **Distinguish a model ceiling from a regression:** if the no-skill baseline
  also fails the task, the skill isn't at fault.
- **Counter-instructions backfire:** piling more selection heuristics on can make
  discovery *worse*, not better. Test any addition against the measured number;
  ship nothing that doesn't move it.
- **Isolate arms:** if Mjolnir's own guidance is active during a "no-skill"
  benchmark, the baseline is secretly running Mjolnir and the gap is fiction.
