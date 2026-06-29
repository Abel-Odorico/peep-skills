---
name: analytics-craft
description: >
  Design and implement gerencial analytics panels — retention metrics, cohort heatmap,
  health banners, WoW (week-over-week) retention, new vs returning users.
  Turns raw data into executive insight. Anti-chart-soup: fewer charts, more decisions.
  Use when user asks for analytics dashboard, retention view, cohort analysis, engagement metrics,
  or invokes /analytics-craft.
---

# Analytics Craft

Build analytics panels that **answer questions, not display data**.

The failure mode of analytics UIs: beautiful charts that communicate nothing actionable. More charts ≠ more insight. One number that drives a decision beats ten charts that describe the past.

---

## The Dual Failure

**Failure 1 — Chart soup:** 15 KPIs, 8 charts, 3 tables. Data everywhere. Decisions nowhere. The executive stares at it and asks "so... is this good or bad?"

**Failure 2 — Pretty but shallow:** Gorgeous area charts with no context. "2,784 views" — is that up? Down? Normal? Alarming?

The goal: **gerencial**. Every element either triggers a decision or builds toward one. If it doesn't, cut it.

---

## Before Any Code

Answer three questions:

**What decision does this metric enable?**
Not "how many users we have." *Should we invest more in acquisition this week, or focus on activation?* The answer shapes which metrics lead.

**What's the health threshold?**
Numbers without context are decorative. Define: what's good, what's a warning, what's critical — before building the UI. Embed these thresholds in the visualization.

**Who reads this and when?**
A founder checking at 7am wants one number and a trend arrow. An analyst wants the cohort table. Same data, different views.

---

## Retention Analytics — The Core Pattern

### What to measure

| Metric | Definition | Why it matters |
|--------|-----------|----------------|
| **New users** | First meaningful action this period | Acquisition |
| **Returning users** | Acted this period AND in a previous period | Stickiness |
| **WoW retention** | % of last period's users who came back this period | Health |
| **Cohort retention** | % of cohort week W still active at week W+N | Long-term retention curve |

### Backend — two endpoints

**`GET /analytics/retention?weeks=N`**

```python
# Weekly new vs returning + WoW retention rate
# 1. Get all bets/actions with user_id + week_start (date_trunc('week', ts)::date)
# 2. first_week per user = min(week_start)
# 3. For each week: active=all users, new=users where first_week==this_week, returning=active-new
# 4. WoW = |active_this ∩ active_prev| / |active_prev|
# Return: { weeks: [{week_start, active, new, returning, wow_retention}], summary: {...} }
```

Key SQLAlchemy pattern (PostgreSQL):
```python
from sqlalchemy import text
rows = db.execute(text("""
    SELECT user_id, date_trunc('week', created_at)::date AS week_start
    FROM your_events_table
    WHERE created_at IS NOT NULL
    GROUP BY user_id, date_trunc('week', created_at)::date
""")).fetchall()
```

**`GET /analytics/cohort`**

```python
# Cohort matrix: for each cohort week, how many users returned at offset +0, +1, +2... weeks
# 1. Same query as above
# 2. first_week per user = cohort
# 3. For each cohort, for each week offset up to latest_week:
#    pct = active_in_cohort_at_offset / cohort_size * 100
# Return: { cohorts: [{cohort_week, size, weeks: [{offset, active, pct}]}], max_offset }
```

Summary object for the banner:
```python
latest = weeks[-1]; prev = weeks[-2] if len >= 2
summary = {
    "latest_active": latest.active,
    "latest_new": latest.new,
    "latest_returning": latest.returning,
    "latest_wow": latest.wow_retention,      # float or None
    "prev_wow": prev.wow_retention,
    "trend": "up" | "down" | "stable"        # compare latest_wow vs prev_wow
}
```

---

## Frontend Architecture

### Component hierarchy

```
RetentionTab
 ├── HealthBanner          ← most important: verdict + primary number
 ├── GrowthChart           ← stacked AreaChart (new + returning)
 ├── WoWRetentionChart     ← BarChart colored by threshold
 └── CohortHeatmap         ← table with HSL gradient cells
```

### 1. Health Banner — the CEO card

One element that answers "is this good or bad?" before any charts.

```jsx
const health = wow >= 50 ? 'great' : wow >= 30 ? 'ok' : 'bad'
const cfg = {
  great: { color: '#22c55e', label: 'SAUDÁVEL',  icon: '✅' },
  ok:    { color: '#f59e0b', label: 'ATENÇÃO',   icon: '⚠️' },
  bad:   { color: '#ef4444', label: 'CRÍTICO',   icon: '🚨' },
}
```

Contents: status label + giant % + trend delta + plain-language sentence + 3 mini KPIs (active/new/returning).

**Anti-pattern:** don't put this at the bottom. It goes first, above all charts.

### 2. Growth Chart — AreaChart (not BarChart)

Stacked areas communicate *composition* better than stacked bars for weekly time series.

```jsx
// Use recharts AreaChart with stackId
<Area dataKey="Retornantes" stackId="1" fill="url(#gRet)" stroke="#3b82f6" />
<Area dataKey="Novos"       stackId="1" fill="url(#gNew)" stroke="#22c55e" />
// Gradients: 55% opacity at top → 10% at bottom
```

Color rule: Retornantes (blue, bottom) → indicates stickiness. Novos (green, top) → indicates acquisition. The ratio visually shows whether growth is organic (more blue) or acquisition-driven (more green).

No dual Y-axis. Keep retention % in a separate chart.

### 3. WoW Retention — colored BarChart

Each bar gets its own color based on threshold:

```jsx
<Cell fill={d.ret >= 50 ? '#22c55e' : d.ret >= 30 ? '#f59e0b' : '#ef4444'} />
```

Add reference lines at thresholds:
```jsx
<ReferenceLine y={50} stroke="#22c55e" strokeDasharray="4 2" label="50% meta" />
<ReferenceLine y={30} stroke="#f59e0b" strokeDasharray="4 2" label="30% limite" />
```

Domain: `[0, 100]`. No dual Y-axis. This chart answers: "Is retention improving or degrading?"

### 4. Cohort Heatmap

Table where cell color = HSL gradient based on % value:

```js
function cellBg(pct) {
  if (pct == null) return { bg: 'var(--bg-overlay)', fg: 'var(--text-4)' }
  // 0%→hue 0 (red), 100%→hue 120 (green), via hue = pct * 1.2
  const h = Math.round(pct * 1.2)
  const alpha = pct > 0 ? 0.25 + pct * 0.006 : 0.08
  return {
    bg: `hsla(${h}, 75%, 38%, ${alpha + 0.35})`,
    fg: pct >= 40 ? '#fff' : 'var(--text-1)',
  }
}
```

Minimum cell width: 52px. Add gradient legend strip at bottom (red→yellow→green).

Diagonal pattern: healthy products show a plateau in the diagonal — retention stabilizes after initial drop. If every week column drops to 0%, users are one-time only.

---

## Design Principles

### Less data, more decisions

Cut anything that doesn't answer: "What should I do differently this week?"

Remove:
- Raw counts when % tells the story
- Multiple tables of the same data
- "Legenda explicativa" cards (embed context inline)
- Dual Y-axis charts when possible (split into two clean charts)

Keep:
- Health verdict (above the fold)
- One trend direction per chart (not 5 lines per chart)
- Plain-language interpretation ("4 em 10 usuários voltam")

### Color semantics — always consistent

| Color | Meaning |
|-------|---------|
| Green (#22c55e) | Good / New users / Saudável |
| Blue (#3b82f6) | Returning / Neutral positive |
| Amber (#f59e0b) | Warning / Atenção |
| Red (#ef4444) | Bad / Crítico |

Never use these colors for decoration. Color always carries semantic meaning.

### Thresholds — define before building

Generic thresholds for weekly retention in engagement apps:
- ≥ 50% WoW = healthy (users reliably return)
- 30–49% = attention (some churn, monitor)
- < 30% = critical (most users don't return)

Adjust per domain: gaming is 60%+, B2B SaaS 40%+, media 20%+ can be ok.

---

## Stack compatibility

This pattern works with any stack that can group events by user+week:

| Backend | Adaptation |
|---------|-----------|
| FastAPI + PostgreSQL | `date_trunc('week', ts)::date` |
| Express + MySQL | `DATE(ts - INTERVAL WEEKDAY(ts) DAY)` |
| Django + PG | Same `date_trunc` via raw SQL or `TruncWeek` |
| Supabase | Direct SQL or Edge Function |

Frontend: works with recharts, chart.js, victory, or even plain CSS (the cohort heatmap is pure table).

---

## Checklist

Before shipping a retention analytics panel:

- [ ] Health banner is first element, above all charts
- [ ] Health verdict is automatic (not "here's the data, you decide")
- [ ] WoW retention % is the hero metric, not raw counts
- [ ] Each bar/cell is colored by threshold (no uniform color)
- [ ] Cohort table has HSL gradient (not binary green/red)
- [ ] No dual Y-axis in the same chart
- [ ] Plain-language sentence explains what the number means
- [ ] Historical average shown alongside current value
- [ ] Trend delta (vs previous period) is explicit
