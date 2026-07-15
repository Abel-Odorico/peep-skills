# peep-skills

Portable agent skills for Codex, Claude Code, OpenCode, frontend craft, analytics, and productivity.

## Install

### Codex

O repositório inclui um catálogo Codex em `.agents/plugins/marketplace.json` e manifestos `.codex-plugin/` nos plugins compatíveis.

### Claude Code

```bash
# 1. Add marketplace
claude plugin marketplace add Abel-Odorico/peep-skills

# 2. Install plugins
claude plugin install frontend-craft@peep-skills
claude plugin install analytics-craft@peep-skills
claude plugin install web-push@peep-skills
claude plugin install telegram-admin-bot@peep-skills
claude plugin install multi-provider-ai@peep-skills
claude plugin install pwa-craft@peep-skills
claude plugin install fastapi-auth@peep-skills
claude plugin install caveman@peep-skills
claude plugin install find-skills@peep-skills
claude plugin install skill-creator@peep-skills
claude plugin install using-superpowers@peep-skills
claude plugin install ai-image-generation@peep-skills
claude plugin install vercel-react-best-practices@peep-skills
claude plugin install shadcn@peep-skills
claude plugin install forge-agent-loop@peep-skills
claude plugin install sandeco-loop@peep-skills
```

### Cursor

This repository also includes project skills under `.cursor/skills/`.

Clone or open this repository in Cursor and the skills are available as project skills:

```text
.cursor/skills/<skill-name>/SKILL.md
```

## Plugins

### forge-agent-loop

Projeta loops de agentes com checks externos, estado retomável, guardrails e estados de parada inequívocos. O mesmo núcleo gera adaptadores para Codex, Claude Code e OpenCode sem duplicar a especificação.

Inspirada conceitualmente na [Sandeco Loop](https://github.com/sandeco/prompts/tree/main/sandeco-loop), com implementação própria e desacoplada de harness.

**Fluxo:** triar → especificar → endurecer → instalar adaptadores opcionais → validar → executar somente sob pedido explícito.

**Invocação:** `$forge-agent-loop` no Codex · `/forge-agent-loop:forge-agent-loop` no Claude Code · skill `forge-agent-loop` no OpenCode.

---

### sandeco-loop

Forja loops de agente com check externo, estado retomável, guardrails reais e adaptadores para Codex, Claude Code e OpenCode. Evolução da Sandeco Loop original com auto-sugestão proativa, quickstart templates e scripts de validação.

**Diferenças do forge-agent-loop:** auto-detecção de oportunidade de loop, quickstart (4 templates prontos), script `forge_loop.py` com 5 subcomandos (init, validate, install-adapters, quickstart, status), dashboard de saúde do loop, integração Cursor, português-BR.

**Fluxo:** triar → descobrir contexto → entrevistar → endurecer → especificar → instalar adaptadores → validar → executar só sob pedido.

**Invocação:** `/sandeco-loop` no Claude · skill `sandeco-loop` no OpenCode · `$sandeco-loop` no Codex.

---

### frontend-craft

Build memorable, production-grade frontend interfaces. Anti-AI-slop.

Fuses two approaches:
- **Bold aesthetic direction** — extreme visual styles, anti-generic fonts, unforgettable composition
- **Craft systems** — token architecture, surface elevation, spacing grid, depth strategy

**Workflow:**
1. Intent first (who, what task, how it feels)
2. Domain exploration (concepts, color world, signature, defaults to kill)
3. Bold aesthetic direction committed upfront
4. Token system built before components
5. Self-critique before showing (swap, squint, signature, unforgettable tests)
6. Save patterns to `system.md` for session memory

**Commands:** `/frontend-craft:status` · `/frontend-craft:audit` · `/frontend-craft:critique`

---

### caveman

Ultra-compressed communication mode. Cuts ~75% of tokens while keeping full technical accuracy.

> Originally by [Julius Brussee](https://github.com/JuliusBrussee) — MIT License.

**Commands:** `/caveman` · `/caveman lite|full|ultra` · `/caveman-commit` · `/caveman-help` · `/caveman-review` · `/compress`

---

### find-skills

Discover and install agent skills from the open skills ecosystem.

> Originally by [Vercel Labs](https://github.com/vercel-labs/skills).

---

### skill-creator

Create, modify, evaluate, benchmark, and improve agent skills.

> Originally by [Anthropic](https://github.com/anthropics/skills).

---

### using-superpowers

Require skill discovery and invocation before agent responses and actions.

> Originally by [Jesse Vincent](https://github.com/obra).

---

### ai-image-generation

Generate and edit AI images with inference.sh models through the belt CLI.

> Originally by [skills-shell](https://github.com/skills-shell/skills).

---

### vercel-react-best-practices

React and Next.js performance optimization guidelines from Vercel Engineering.

> Originally by [Vercel Labs](https://github.com/vercel-labs/agent-skills).

---

### shadcn

Manage shadcn/ui components and projects: adding, searching, debugging, styling, and composing UI.

> Originally by [shadcn](https://github.com/shadcn/ui).

---

### analytics-craft

Design and implement gerencial analytics panels — retention metrics, cohort heatmap, health banners, WoW (week-over-week) retention, new vs returning users.

Turns raw data into executive insight. Anti-chart-soup: fewer charts, more decisions.

**Pattern:** Health banner first (SAUDÁVEL/ATENÇÃO/CRÍTICO) → stacked AreaChart (growth) → colored BarChart (retention trend) → cohort heatmap with HSL gradient.

**Backend:** FastAPI/Express/Django patterns for `/retention` and `/cohort` endpoints with PostgreSQL `date_trunc('week', ...)`.

**Commands:** `/analytics-craft`

---

### web-push

Implement Web Push notifications (VAPID) in any PWA — backend subscription storage, per-notification-type URL/tag routing, service worker push handler, and the common gotchas tutorials skip.

**Covers:** tag collision fix, expired subscription cleanup (410), per-type routing config dict, iOS limitations, `renotify`, SW cache versioning.

**Commands:** `/web-push`

---

### telegram-admin-bot

Wire up a Telegram bot for SaaS admin: daily reports, interactive webhook menu, new-user notifications, broadcast messages.

**Covers:** webhook security (secret token + allowlist), HTML parse_mode (never MarkdownV2), `html.escape()` for dynamic values, inline keyboard menus with `editMessageText`, timezone-aware daily report loop (BRT), background task notifications, and 6 gotchas including the silent MarkdownV2 failure mode.

**Commands:** `/telegram-admin-bot`

---

### multi-provider-ai

Route AI requests across OpenRouter and Google Gemini with automatic fallback. Config in DB — no redeploy on key change.

**Covers:** `_get_provider_chain()` pattern, OpenRouter REST + Gemini REST, forced provider order for critical flows, JSON output extraction (regex fallback for Gemini), background task `db.rollback()` safety, free model reference (2026-06), and gotchas (silent 429, `generationConfig` nesting, token truncation).

**Commands:** `/multi-provider-ai`

---

### pwa-craft

Ship a production PWA: cache versioning, network-first API + cache-first assets, offline fallback, iOS safe area, install prompt.

**Covers:** SW registration in `main.jsx` (not `App.jsx`), cache version bump pattern, `clients.claim()` only (never `w.navigate()`), `useInstallPrompt` hook for Android + iOS, `viewport-fit=cover` for safe area, `manifest.json` with screenshots, offline.html pre-cache, and 7 gotchas including the `skipWaiting` + navigate reload loop.

**Commands:** `/pwa-craft`

---

### fastapi-auth

Complete auth for FastAPI: JWT + bcrypt, forgot/reset password with email, rate limiting, Alembic + legacy DDL migration path.

**Covers:** `OAuth2PasswordBearer`, `python-multipart` requirement, `ExpiredSignatureError` before `JWTError`, `_utcnow()` helper (Python 3.12+), antisnoop 202 forgot-password, RFC email headers for Gmail delivery, STARTTLS on 587, token delete-before-create race safety, bcrypt rounds in tests, Alembic + legacy DDL coexistence.

**Commands:** `/fastapi-auth`
