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
claude plugin install security-review@peep-skills
claude plugin install security-hardening-loop@peep-skills
claude plugin install mjolnir@peep-skills
claude plugin install archify@peep-skills
claude plugin install scroll-world@peep-skills
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

> Mantida por histórico/compatibilidade. Para projetos novos use **sandeco-loop** abaixo — mesmo núcleo, mais recursos. Não instale os dois juntos: as descrições de trigger se sobrepõem e podem disparar o plugin errado.

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

### security-review

AI-powered security scanner that reasons about the codebase like a human researcher — traces data flows across files, self-verifies findings to cut false positives, rates severity (CRITICAL→INFO) and proposes a patch for every finding. Nothing is auto-applied.

**Workflow:** scope resolution → dependency audit (CVEs) → secrets & exposure scan → vulnerability deep scan (injection, auth/access control, data handling, crypto, business logic) → self-verification → report.

**References:** language patterns (JS/TS, Python, Java, PHP, Go, Ruby, Rust), secret regex + entropy heuristics, vulnerable package watchlist, vuln categories, report format.

> Originally by [GitHub](https://github.com/github/awesome-copilot) — awesome-copilot.

**Commands:** `/security-review` · `/security-review <path>`

---

### security-hardening-loop

Loop autônomo de hardening: onde o security-review **relata**, este **conserta**. Escaneia com a mesma metodologia, prioriza por severidade e corrige um achado por iteração — cada fix só é aceito se todos os checks operacionais (testes, health endpoint, status de serviço) continuarem ≥ baseline; senão rollback automático via git.

**Núcleo (princípios sandeco-loop):** baseline operacional antes de tocar em código → fila em `.security-loop/state.json` (retomável) → PICK → FIX → CHECK → COMMIT ou ROLLBACK → paradas nomeadas (sucesso, sem-progresso, check-quebrado, esgotamento, bloqueio).

**Guardrails:** um achado por commit, nunca em working tree suja, nunca push/deploy/restart de produção sem pedido, rotação de secrets sempre tarefa humana, major bumps viram bloqueio, anti-autoengano (proibido afrouxar check para o fix passar).

**References:** protocolo do loop + schema de estado, checks de operação por stack (PHP, Node, Python, Docker, systemd), playbooks de fix mínimo por categoria (SQLi, XSS, secrets, IDOR, JWT, crypto, deps).

**Commands:** `/security-hardening-loop` · `/security-hardening-loop <path>`

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

---

### mjolnir

Context Operating System for coding agents: loads the *right* context, not the *maximum*. On broad "understand/map/audit" tasks it replaces read-everything with investigate-then-load — ~68% fewer tokens and 82% fewer whole-file reads reaching the same answer.

**Covers:** 18-rule doctrine + investigate-don't-search mode; progressive expansion in 4 levels (structure → signatures → single method → whole file, never skip); zero-dependency Python toolkit (`dna`, `index`, `graph`, `symbols`, `slice`, `score`, `find`, `filter_output`, `verify`, `bench`, `harvest`); content-hash caching; output compression with recovery tee; secret guard that refuses credential files; self-tested (61 checks passing).

**Commands:** `/mjolnir` (auto-triggers on large/unfamiliar repos and broad comprehension tasks).

### archify

Professional technical diagrams (architecture, workflow, sequence, data-flow, lifecycle/state) as self-contained HTML files with inline SVG, persistent dark/light theme toggle, and one-click export to PNG (up to 4×) / JPEG / WebP / dual-theme SVG. Accepts plain-language descriptions or pasted Mermaid code (`flowchart`, `sequenceDiagram`, `stateDiagram`) and lays diagrams out from scratch in archify style.

**Covers:** typed JSON IR per diagram type with JSON Schemas + standalone validators (no install needed); zero-dependency Node (>=18) renderers with layout checks (node/label overlap, arrow routing, legend bounds); `node bin/archify.mjs render|validate|check|doctor|demo` CLI; optional trace animation respecting `prefers-reduced-motion`; worked examples for all five modes.

**Use nos fluxos Peep:** mapear arquitetura de um repo antes de mexer, desenhar fluxo de deploy, sequência de chamadas de API, pipelines de dados — o HTML gerado abre por `file://` e o SVG dual-theme cola direto em README.

Based on [tt-a1i/archify](https://github.com/tt-a1i/archify) (MIT, rewrite of Cocoon-AI/architecture-diagram-generator).

### scroll-world

Landing page com câmera cinematográfica guiada por scroll: mergulha de fora pra dentro de cada cena e voa pra próxima sem cortes — uma tomada contínua (estilo Emons/Apple product page). Entrevista tema, brand kit, direção de arte, roteiro de cenas, versão mobile (9:16 nativo) e orçamento (créditos estimados) antes de gerar qualquer coisa.

**Covers:** pipeline Higgsfield completo (stills → clipes "dive-in" → conectores costurados frame-a-frame pra emenda invisível); modelos com frame-lock (`seedance_2_0`, `seedance_2_0_mini`, `kling3_0`); scrub engine vanilla JS portátil (blob-seek, lazy load, crossfade de emenda, hardening mobile: iOS priming, safe-area, seek-coalescing); knockout de fundo pra cenas flutuantes.

**Requer:** Higgsfield CLI autenticada com créditos, `ffmpeg`/`ffprobe`, Python 3 + Pillow. Codex CLI opcional (gera os stills sem gastar créditos Higgsfield, cobrado na assinatura ChatGPT).

**⚠️ Custo:** não é gratuita — cada build gasta créditos Higgsfield (N stills + (2N-1) vídeos, dobra se mobile). A skill calibra custo real antes de gerar e pede aprovação.

Based on [oso95/scroll-world](https://github.com/oso95/scroll-world) (MIT).

---

## Ferramentas externas (não incluídas neste repo)

### Mira (mira-animator)

Agentes e templates para criar apresentações HTML animadas com D3.js. **Não é um plugin deste repositório** — é um pacote npm de terceiro, [`mira-animator`](https://github.com/sandeco/mira-animator) por [sandeco](https://github.com/sandeco), licenciado sob **PolyForm-Noncommercial-1.0.0**. Por causa dessa licença o código/templates do Mira não são redistribuídos aqui.

**Instalação (no projeto onde você quer gerar slides):**

```bash
npx mira-animator@latest install
```

O instalador cria as skills (`mira-new`, `mira-planner`, `mira-builder`, `mira-animator` etc.), a pasta `mira-templates/` (themes, engines, vendor) e `mira.config.json` na raiz do projeto. Funciona em Claude Code, Codex e OpenCode; Cursor lê as skills instaladas em `.cursor/skills/` automaticamente.

Pipeline típico: `/mira-new` → `/mira-extract` → `/mira-planner` → `/mira-copywriter` → `/mira-builder` + `/mira-animator` → `/mira-validator`.

**Uso comercial:** a licença PolyForm-Noncommercial proíbe uso comercial do pacote. Confirme com o autor (sandecom@gmail.com) ou avalie uma licença comercial antes de usar em contexto de negócio.
