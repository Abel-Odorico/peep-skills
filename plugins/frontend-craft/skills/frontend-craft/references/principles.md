# Craft Principles — Code Reference

Concrete values and CSS examples backing the SKILL.md principles.

---

## Surface Elevation — Dark Mode

```css
:root {
  --base:      hsl(220 13% 9%);   /* canvas */
  --surface-1: hsl(220 13% 11%);  /* cards, panels */
  --surface-2: hsl(220 13% 13%);  /* dropdowns, popovers */
  --surface-3: hsl(220 13% 16%);  /* nested overlays */
  --overlay:   hsl(220 13% 20%);  /* modals */
}
```

Jumps: ~2% lightness per level. Feel it, don't see it.

## Surface Elevation — Light Mode

```css
:root {
  --base:      hsl(0 0% 98%);
  --surface-1: hsl(0 0% 100%);
  --surface-2: hsl(0 0% 100%);   /* + box-shadow instead */
  --surface-3: hsl(0 0% 100%);
}
```

## Borders

```css
/* Dark mode */
--border-subtle:  rgba(255,255,255,0.04);
--border:         rgba(255,255,255,0.08);
--border-strong:  rgba(255,255,255,0.12);
--border-focus:   rgba(255,255,255,0.24);

/* Light mode */
--border-subtle:  rgba(0,0,0,0.04);
--border:         rgba(0,0,0,0.08);
--border-strong:  rgba(0,0,0,0.12);
--border-focus:   rgba(0,0,0,0.24);
```

## Depth Strategies

```css
/* Borders-only */
border: 0.5px solid var(--border);

/* Single shadow */
box-shadow: 0 1px 3px rgba(0,0,0,0.08);

/* Layered (premium) */
box-shadow:
  0 0 0 0.5px rgba(0,0,0,0.05),
  0 1px 2px rgba(0,0,0,0.04),
  0 2px 4px rgba(0,0,0,0.03),
  0 4px 8px rgba(0,0,0,0.02);

/* Surface color (no shadows) — use background tokens only */
```

## Text Hierarchy

```css
--text-primary:   hsl(220 13% 95%);
--text-secondary: hsl(220 13% 65%);
--text-tertiary:  hsl(220 13% 45%);
--text-muted:     hsl(220 13% 30%);
```

## Typography — Pairing Examples

Do NOT copy these. Use as inspiration for the right pairing for your specific domain.

```
Editorial/magazine:   "Playfair Display" + "Source Serif 4"
Terminal/hacker:      "Berkeley Mono" + "IBM Plex Mono"  
Luxury/refined:       "Cormorant Garamond" + "Jost"
Brutalist/raw:        "Bebas Neue" + "Space Mono"
Warm/notebook:        "Lora" + "Nunito"
Industrial:           "DM Mono" + "DM Sans"
Art deco:             "Josefin Sans" + "Libre Baskerville"
```

Import pattern:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DISPLAY:wght@400;700&family=BODY:wght@400;500&display=swap" rel="stylesheet">
```

## Data Typography

```css
.data-value {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}
```

## Spacing Scale

```css
/* Base: 4px */
--space-1:  4px;   /* micro */
--space-2:  8px;   /* tight */
--space-3:  12px;
--space-4:  16px;  /* component */
--space-5:  20px;
--space-6:  24px;  /* section */
--space-8:  32px;
--space-10: 40px;
--space-12: 48px;  /* major */
--space-16: 64px;
```

## Border Radius Scale

```css
/* Technical/dense */
--radius-sm: 2px;
--radius-md: 4px;
--radius-lg: 6px;
--radius-xl: 8px;

/* Friendly/approachable */
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
```

## Animation

```css
/* Micro-interactions */
transition: background 150ms ease-out,
            color 150ms ease-out,
            border-color 150ms ease-out;

/* Larger transitions */
transition: transform 220ms cubic-bezier(0.0, 0.0, 0.2, 1),
            opacity 220ms ease-out;

/* Staggered page load */
.item { animation: fadeUp 400ms ease-out both; }
.item:nth-child(1) { animation-delay: 0ms; }
.item:nth-child(2) { animation-delay: 60ms; }
.item:nth-child(3) { animation-delay: 120ms; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

## Visual Atmosphere

```css
/* Noise texture overlay */
.noise::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,...");
  opacity: 0.03;
  pointer-events: none;
}

/* Gradient mesh background */
background:
  radial-gradient(ellipse at 20% 50%, hsla(220,70%,20%,0.3) 0%, transparent 60%),
  radial-gradient(ellipse at 80% 20%, hsla(280,60%,15%,0.2) 0%, transparent 60%),
  var(--base);

/* Grain overlay with SVG */
filter: url(#grain);
```

## Control Tokens

```css
--control-bg:     var(--surface-1);  /* or slightly darker */
--control-border: var(--border);
--control-focus:  var(--brand);

input, [role="combobox"] {
  background: var(--control-bg);
  border: 1px solid var(--control-border);
  outline: 2px solid transparent;
}

input:focus {
  border-color: var(--control-focus);
  outline-color: rgba(var(--brand-rgb), 0.2);
}
```

## Dark Mode — Semantic Color Adjustments

Desaturate status colors slightly for dark backgrounds:

```css
/* Light mode: vivid */
--success: hsl(142 72% 29%);
--warning: hsl(37 92% 50%);
--error:   hsl(0 84% 60%);

/* Dark mode: slightly desaturated + lighter */
--success: hsl(142 50% 55%);
--warning: hsl(37 70% 65%);
--error:   hsl(0 70% 65%);
```

## Sidebar Pattern

```css
/* Same background as canvas — NOT different color */
.sidebar {
  background: var(--base);
  border-right: 1px solid var(--border);
  /* No different background-color */
}
```

## Card Grid Variety

Avoid monotonous equal grids. Mix:

```css
/* Feature grid — first card spans 2 columns */
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}
.card:first-child { grid-column: span 2; }

/* Masonry-like with CSS columns */
.grid {
  columns: 3;
  column-gap: 16px;
}
.card { break-inside: avoid; margin-bottom: 16px; }

/* Bento layout */
.grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  grid-template-rows: auto;
}
```
