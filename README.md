# peep-skills

Claude Code skills for frontend craft, analytics, and productivity.

## Install

### Claude Code

```bash
# 1. Add marketplace
claude plugin marketplace add Abel-Odorico/peep-skills

# 2. Install plugins
claude plugin install frontend-craft@peep-skills
claude plugin install analytics-craft@peep-skills
claude plugin install web-push@peep-skills
claude plugin install caveman@peep-skills
claude plugin install find-skills@peep-skills
claude plugin install skill-creator@peep-skills
claude plugin install using-superpowers@peep-skills
claude plugin install ai-image-generation@peep-skills
claude plugin install vercel-react-best-practices@peep-skills
claude plugin install shadcn@peep-skills
```

### Cursor

This repository also includes project skills under `.cursor/skills/`.

Clone or open this repository in Cursor and the skills are available as project skills:

```text
.cursor/skills/<skill-name>/SKILL.md
```

## Plugins

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
