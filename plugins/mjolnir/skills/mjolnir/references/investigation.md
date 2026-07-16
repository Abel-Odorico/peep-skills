# Investigation Mode — understand before reading

Load for non-trivial "why/how/where" tasks. Mjolnir doesn't search a repo, it
**investigates** it: form hypotheses, rank them, gather evidence, open only the
most promising code. Load evidence, not files.

## The detective loop

```
observe → hypotheses → rank by confidence → gather evidence → drop weak → confirm root cause → load only what's needed → answer → stop
```

Example — "login takes 8s": hypotheses = DB latency (42%), Redis (31%), JWT
validation (18%), external API (9%). Rank first; open code for the top
hypothesis only. Promote/demote as evidence lands.

## Read the DNA first (`dna.py`)

Detect stack + architecture, then search where projects of that shape keep
things — not blind. NestJS → `src/modules/`; Laravel → `app/Http/Controllers`,
`app/Models`; Next.js → `app/`, `lib/`, `actions/`. Recognize the pattern
(MVC, DDD, hexagonal, CQRS, monorepo) and let it steer discovery.

## Intent templates — each intent has its own search strategy

| Intent | Investigate, in order |
|---|---|
| Performance | cache · DB queries/indexes · N+1 loops · external HTTP · hot paths |
| Bug | stack trace · definition · call graph · imports · usages · tests |
| Feature | entry point · controller · service · persistence · UI · config |
| Refactor | the symbol · its consumers · interfaces · side effects · tests |

## Root cause, with evidence

Never just locate code — state the probable cause, its confidence, the evidence
for it, and the alternatives you rejected. A conclusion without evidence is a
guess. Gather evidence cheaply: `find.py <concept>` locates it as enclosing
symbols, `slice.py <file> <symbol>` reads only that body, and `graph.py --path` /
`--importers` turn a hunch into a proven edge.

## Impact before change (`graph.py --importers`)

Before modifying a symbol, list what depends on it — callers, importers, tests,
consumers. Changing `AuthService` touches its controller, middleware, refresh
flow, and N tests. The caller set is mandatory context, never optional.

## Semantic navigation

The user asks in concepts ("authentication"), the code lives in files. Map the
concept to its chain — login → JWT → refresh → middleware — and walk it with
`graph.py --path a b` / `--cluster`. Questions become graph traversals.

## Scope and dependency radius

Estimate the minimum files a change needs and stop expanding at the dependency
radius (callers + direct deps). "Fix login validation" ≈ 2 files — don't inspect
tests/payments/email. Predict cost first with `token_estimate.py` / `bench.py`.

## Dead code stays out (`graph.py --orphans`)

Orphans (imported by nothing, not an entry point), obsolete modules, and
duplicate implementations never enter context unless the task is about them.

## Adaptive strategy by repo size

- **Small:** a direct grep/read is fine — skip the machinery.
- **Medium:** `graph.py` + `symbols.py` (structure + signatures).
- **Large / monorepo:** `dna.py` → plan → `--cluster` discovery → progressive
  expansion. Never use the large-repo strategy on a small one.

## Evidence beats assumption (hallucination shield)

If confidence is below threshold, do not guess — expand investigation instead.
`<60` need more · `60–85` probably enough · `>90` stop. Track what's already
confirmed and don't rediscover it; record dead ends and don't revisit them.

## Investigation metrics (report if useful)

files inspected vs avoided · summaries/cache reused · hypothesis accuracy · token
savings · how confidence evolved. Makes the reasoning transparent and cheap to
resume.

## The point

Search finds files. Investigation finds evidence. The goal isn't to read more
code — it's to understand more while reading less.
