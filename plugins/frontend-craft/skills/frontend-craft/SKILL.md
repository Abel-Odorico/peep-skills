---
name: frontend-craft
description: Build memorable, production-grade frontend interfaces — dashboards, SaaS apps, components, pages, marketing sites. Fuses bold aesthetic direction with rigorous craft systems. Anti-AI-slop. Use when building any web UI.
---

# Frontend Craft

Build interfaces that are **memorable and precise** — bold aesthetic vision executed through craft systems.

## Scope

**Use for:** Dashboards, SaaS apps, admin panels, landing pages, components, tools, marketing sites — any web UI.

---

# The Dual Failure

Interfaces fail in two ways.

**Failure 1 — Generic craft:** Token systems, elevation hierarchy, spacing grid — executed perfectly. And the result is indistinguishable from 10,000 other AI-generated interfaces. Correct but forgettable. Safe but invisible.

**Failure 2 — Aesthetic without discipline:** Bold typography, unexpected color, dramatic layout — executed on top of random hex values, inconsistent spacing, no elevation system. Impressive at first glance. Falls apart on inspection. Memorable but broken.

The goal: **neither**. Unforgettable aesthetic, executed with system precision.

---

# Before Any Code

Answer three questions with specifics. Not in your head — out loud.

**Who is this human?**
Not "users." The actual person. Where are they when they open this? What did they do 5 minutes ago? A teacher at 7am, a developer debugging at midnight, a founder between investor meetings — completely different interfaces.

**What must they accomplish?**
The verb. Not "use the app." *Grade these submissions. Find the broken deployment. Approve the payment.* The answer determines what leads, what follows, what hides.

**What should this feel like?**
Name it with words that mean something. "Clean and modern" means nothing. Warm like a notebook? Cold like a terminal? Dense like a trading floor? Brutal like a command line? Luxe like a private bank? Playful like a toy? This shapes everything.

If you cannot answer these with specifics — ask. Do not guess. Do not default.

---

# Aesthetic Direction

Before exploring the domain, commit to a bold aesthetic direction. Not safe — bold. Pick an extreme and execute it with precision:

- Brutally minimal
- Maximalist density
- Retro-futuristic
- Organic / natural
- Luxury / refined
- Playful / toy-like
- Editorial / magazine
- Brutalist / raw
- Art deco / geometric
- Soft / pastel
- Industrial / utilitarian
- Terminal / hacker
- Or something truer to this specific context

**CRITICAL:** Choose and commit. Bold maximalism and refined minimalism both work — the key is intentionality, not intensity.

**The unforgettable test:** What's the ONE thing someone will remember about this interface 3 days later? If you can't name it before building, you haven't chosen a direction.

---

# Domain Exploration

Generic output: task type → visual template → theme.  
Crafted output: task type → product domain → signature → structure + expression.

Spend real time in the product's world before any visual decisions.

## Required Outputs

**Do not propose any direction until you produce all four:**

**Domain:** Concepts, metaphors, vocabulary from this product's world. Not features — territory. Minimum 5.

**Color world:** What colors exist in this domain naturally? Not "warm" or "cool" — go to the actual world. If this product were a physical space, what would you see? List 5+ colors that belong there and nowhere else.

**Signature:** One element — visual, structural, or interaction — that could only exist for THIS product. Something unforgettable. If you can't name one, explore deeper.

**Defaults to kill:** 3 obvious choices for this interface type. Name them explicitly so you can consciously reject them.

## Proposal

Direction must explicitly reference:
- Domain concepts explored
- Colors from the color world
- The signature element  
- What replaces each default

**The identity test:** Remove the product name from your proposal. Could someone identify what this is for? If not — generic. Explore deeper.

---

# Typography Rules

Typography IS the design, not a container for it.

**NEVER use:** Inter, Roboto, Arial, system-ui, Space Grotesk, or any font you've used recently. Convergent fonts signal AI immediately.

**Always:** Pair a distinctive display font with a refined body font. The pairing should feel designed for this specific product — a trading terminal and a meditation app need completely different type.

Build distinct levels distinguishable at a glance:
- **Display/Headlines** — weight + tight tracking for presence
- **Body** — comfortable weight for readability
- **Labels/UI** — medium weight, works at small sizes
- **Data** — monospace + `tabular-nums` for alignment

Don't rely on size alone. Combine size, weight, letter-spacing. If you squint and can't separate headline from body, the hierarchy is too weak.

---

# Color Rules

**NEVER:** Purple gradients on white. Generic blue accents. Evenly-distributed palettes. Safe neutrals.

**Always:** Color comes FROM somewhere — the product's world, not applied TO it. Your palette should feel like it arrived from a specific place.

**Commit to dominant colors with sharp accents.** One accent used with intention beats five colors used without thought.

Gray builds structure. Color communicates — status, action, emphasis, identity. Unmotivated color is noise.

**Beyond temperature:** Is this quiet or loud? Dense or spacious? Serious or playful? Geometric or organic? Find the specific quality, not the generic label.

---

# Spatial Composition

**Reject monotonous layouts.** Same card size, same gaps, same density everywhere — the sound of no one deciding.

Pursue:
- **Asymmetry** — balanced without being symmetrical
- **Overlap** — elements breaking container boundaries
- **Diagonal flow** — eye movement with purpose
- **Grid-breaking elements** — one thing that escapes the grid deliberately
- **Varied density** — dense tooling areas breathing into open content
- **Generous negative space OR controlled density** — pick one, commit

Focal point: every screen has one thing the user came here to do. That thing dominates — through size, position, contrast, or the space around it.

---

# Visual Atmosphere

Create depth and atmosphere rather than defaulting to solid backgrounds:

- Gradient meshes
- Noise / grain textures
- Geometric patterns
- Layered transparencies
- Dramatic shadows
- Decorative borders
- Custom cursors (when appropriate)
- Scroll-triggering effects
- Hover states that surprise

Match complexity to the aesthetic vision. Maximalist needs elaborate effects. Minimal needs precision and restraint. **Elegance is executing the vision well — not complexity for its own sake.**

---

# Motion

One well-orchestrated page load with staggered reveals creates more delight than scattered micro-interactions.

- **Micro-interactions** (hover, focus): ~150ms, instant feel
- **Transitions** (modals, panels): 200-250ms, deceleration easing
- **Page load**: staggered reveals with `animation-delay`, meaningful sequence
- **Scroll-triggering**: elements that respond to scroll position

Use CSS-only for HTML. Use Motion library for React when available.

**NEVER** spring/bounce in professional interfaces. Avoid animation that distracts from content.

---

# Token Architecture

Every color traces to primitives. No random hex values.

```
Foreground   → text/primary, text/secondary, text/tertiary, text/muted
Background   → base, surface-1, surface-2, surface-3, overlay
Border       → default, subtle, strong, stronger (focus)
Brand        → primary accent
Semantic     → destructive, warning, success, info
Control      → bg, border, focus (separate from surfaces)
```

**Token names carry world.** `--ink` and `--parchment` evoke a place. `--gray-700` evokes nothing. Someone reading only your tokens should guess the product.

## Surface Elevation

Surfaces stack. Build it as a system:

```
Level 0: Canvas (app background)
Level 1: Cards, panels
Level 2: Dropdowns, popovers
Level 3: Nested overlays
Level 4: Highest (rare)
```

Dark mode: higher elevation = slightly lighter (few % points, not dramatic)  
Light mode: higher elevation = slightly lighter OR subtle shadow

**The subtlety principle:** You can barely see the difference in isolation. But when surfaces stack, hierarchy emerges. Whisper-quiet shifts that you feel rather than see.

**Sidebars:** Same background as canvas + subtle border. Not a different color — that fragments the space.  
**Inputs:** Slightly darker than surroundings — inset, receives content.  
**Dropdowns:** One level above parent surface.

## Text Hierarchy

Four levels, not two:
- **Primary** — highest contrast, default text
- **Secondary** — supporting text, slightly muted
- **Tertiary** — metadata, timestamps
- **Muted** — disabled, placeholder

## Border Progression

Not binary — a scale:
- **Subtle** — softest separation
- **Default** — standard borders
- **Strong** — hover states, emphasis
- **Stronger** — focus rings, maximum emphasis

Borders: low opacity rgba, not solid hex. `rgba(0,0,0,0.08)` not `#e5e7eb`. They disappear when you're not looking, findable when you need structure.

---

# Depth Strategy

**Pick ONE. Commit. No mixing.**

| Strategy | When | CSS |
|----------|------|-----|
| Borders-only | Technical, dense, utility tools | `0.5px solid rgba(0,0,0,0.08)` |
| Subtle single shadow | Approachable, gentle depth | `0 1px 3px rgba(0,0,0,0.08)` |
| Layered shadows | Premium, dimensional, card presence | Multiple shadow layers |
| Surface color shifts | Hierarchy through tones, no shadows | Different bg values |

---

# Spacing System

Base unit: 4px or 8px. Everything a multiple. No exceptions.

Scale:
- Micro (2-4px): icon gaps, tight pairs
- Component (8-16px): within buttons, inputs
- Section (24-32px): between related groups
- Major (48-64px): distinct sections

Symmetrical padding — TLBR must match unless content demands asymmetry.

---

# Controls

**NEVER** native `<select>`, `<input type="date">`, or unstyled form elements. Build custom:
- Select: trigger button + positioned dropdown
- Date: input + calendar popover
- Checkbox/radio: styled div with state management

Custom triggers: `display: inline-flex; white-space: nowrap` — text + chevron same row.

---

# States

Every interactive element needs:
- Default, hover, active, focus, disabled

Every data element needs:
- Loading, empty, error

Missing states feel broken.

---

# Before Writing Each Component

**Mandatory checkpoint.** State this before every component:

```
Aesthetic: [the bold direction committed to]
Intent:    [who, what task, how it should feel]
Palette:   [colors from domain exploration — WHY they fit]
Type:      [typeface choice — WHY it fits the direction]
Depth:     [chosen strategy — borders/shadows/surface]
Surfaces:  [elevation scale values]
Spacing:   [base unit]
Signature: [where the signature element appears here]
```

If you can't explain WHY for each — you're defaulting. Stop and think.

---

# The Mandate

**Before showing the user — look at what you made.**

Ask: "If they said this lacks craft, what would they mean?"

That thing you just thought of — fix it first.

**The swap test:** If you swapped your typeface for your usual one, would anyone notice? If you swapped the layout for a standard template, would it feel different? Places where swapping wouldn't matter = places you defaulted.

**The squint test:** Blur your eyes. Hierarchy still visible? Nothing harshly jumping out? Craft whispers.

**The signature test:** Can you point to five specific elements where the signature appears? Not "the overall feel" — actual components. A signature you can't locate doesn't exist.

**The token test:** Read your CSS variables out loud. Do they sound like this product, or could they belong to any project?

**The identity test (again):** Remove the product name. Can someone identify what this is for?

**If any check fails — iterate before showing.**

---

# Avoid

**Visual:**
- Purple gradients on white (or any clichéd color scheme)
- Inter, Roboto, Arial, Space Grotesk, system fonts
- Overused font families — vary across every generation
- Harsh borders (first thing you see = too strong)
- Dramatic surface jumps (whisper, not shout)
- Pure white cards on colored backgrounds
- Thick decorative borders
- Gradients/color as pure decoration (color should mean something)
- Multiple accent colors
- Different hues across surfaces (same hue, shift lightness only)

**Structural:**
- Monotonous card grids (same size, same gaps, everywhere)
- Missing navigation context (floating tables feel like component demos)
- Inconsistent spacing (clearest sign of no system)
- Mixed depth strategies
- Missing states (hover, focus, disabled, loading, empty, error)
- Native form elements for styled UI
- Scattered micro-animations (do less, do it well)

**CSS:**
- Random hex values (use token system)
- Negative margins undoing parent padding
- Calc() as workaround (find the clean solution)
- Absolute positioning to escape layout flow

---

# Workflow

## Discovery
```
Domain: [5+ concepts from the product's world]
Color world: [5+ colors that exist in this domain]
Aesthetic: [committed bold direction]
Signature: [one element unique to this product]
Killing: [default 1] → [alternative], [default 2] → [alternative], [default 3] → [alternative]

Direction: [approach referencing all of the above]
```

Ask: "Does that direction feel right?"

## Execution
1. **Explore** — domain, color world, signature, defaults
2. **Propose** — bold direction referencing all four
3. **Confirm** — user buy-in
4. **Build** — token system first, then components
5. **Mandate** — run all checks before showing
6. **Save** — offer to persist patterns

## If `system.md` exists
Read `.frontend-craft/system.md`. Decisions are made. Apply them.

## If no `system.md`
Explore first. Propose. Confirm. Then build.

---

# After Each Task

Always offer:
```
"Want me to save these patterns for future sessions?"
```

If yes, write to `.frontend-craft/system.md`:
- Aesthetic direction and feel
- Typeface choices (display + body)
- Palette (primitives + their values)
- Depth strategy
- Spacing base unit
- Signature element
- Key component patterns

Save when: component used 2+ times, reusable across project, specific measurements worth keeping. Don't save one-offs or temporary experiments.

---

# References

- `references/principles.md` — Token examples, CSS values, dark mode specifics
- `references/critique.md` — Full post-build critique protocol

# Commands

- `/frontend-craft:status` — Current system state
- `/frontend-craft:audit` — Check code against system.md
- `/frontend-craft:extract` — Extract patterns from existing code
- `/frontend-craft:critique` — Craft critique, then rebuild what defaulted
