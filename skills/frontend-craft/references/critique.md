# Critique Protocol

First build shipped the structure. Now look at it the way a design lead reviews a junior's work — not "does this work?" but "would I put my name on this?"

---

## The Gap

Correct: layout holds, grid aligns, colors don't clash.  
Crafted: someone cared about every decision down to the last pixel.

You can feel the difference immediately — the way you tell a hand-thrown mug from an injection-molded one. Both hold coffee. One has presence.

Your first output lives in correct. This critique pulls it toward crafted.

---

## 1. See the Aesthetic Direction

Step back and ask: Is the bold direction you committed to actually visible?

- Can you point to it? Not "the overall feel" — specific elements.
- Would someone describe this interface in the same words you used to describe the direction?
- Is the signature element actually there, or did it get softened away?

If the direction got diluted during implementation — rebuild what diluted it.

---

## 2. See the Composition

Does the layout have rhythm? Great interfaces breathe unevenly — dense tooling areas give way to open content, heavy elements balance against light ones, the eye travels through the page with purpose.

Are proportions doing work? A 280px sidebar says "navigation serves content." A 360px sidebar says "these are peers." If you can't articulate what your proportions are saying, they're saying nothing.

Is there a clear focal point? Every screen has one thing the user came here to do. That thing should dominate. When everything competes equally, nothing wins.

---

## 3. See the Craft

Move close. Pixel-close.

**Spacing:** Every value a multiple of your base unit? No exceptions. But correctness alone isn't craft — a tool panel at 16px padding feels workbench-tight, the same card at 24px feels like a brochure.

**Typography:** Size alone is not hierarchy. Can you distinguish headline from body from label by weight and tracking alone, without size? If not — too flat.

**Surfaces:** Remove every border mentally. Can you still perceive structure through surface color alone? Surfaces should whisper hierarchy. Not thick borders, not dramatic shadows.

**States:** Every button, link, clickable region — hover and press. A subtle shift, not dramatic. Missing states make an interface feel like a photograph of software.

---

## 4. See the Content

Read every visible string as a user would. Not for typos — for truth.

Does this screen tell one coherent story? Could a real person at a real company be looking at exactly this data right now? Or does the page title belong to one product and the sidebar metrics to another?

Content incoherence breaks the illusion faster than any visual flaw.

---

## 5. See the Structure

Open the CSS. Find the lies — places that look right but are held together with tape.

- Negative margins undoing parent padding → use flex column + section-level padding
- Calc() values as workarounds → find the clean layout solution
- Absolute positioning to escape flow → redesign the container
- Random hex values → map to token system

The correct answer is always simpler than the hack.

---

## 6. The Unforgettable Test

After everything:

**What's the ONE thing someone will remember about this interface 3 days later?**

If you can't name it — that's the problem. Find it or create it.

---

## Run in Order

1. Aesthetic direction: visible? signature present?
2. Composition: rhythm, proportions, focal point
3. Craft: spacing, type, surfaces, states
4. Content: coherent story
5. Structure: no CSS hacks
6. Unforgettable: what's the one thing?

Fix what fails. Then ask again. The critique is the design.
