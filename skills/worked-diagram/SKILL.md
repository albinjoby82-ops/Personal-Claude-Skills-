---
name: worked-diagram
description: Explain any EE, DE, computer engineering or calculus concept with one clean inline worked diagram plus short steps and a check question. Use whenever Albin asks to explain, show or diagram something.
category: study
tags: [diagrams, explain, worked-example, ee, de, ce, calculus]
---

# Worked diagram

Albin learns best by seeing the working laid out, not reading about it. Every explanation is: **one worked diagram, then a few short lines, then one check question.** Keep words to a minimum (he is dyslexic and dislikes long text).

## When to use
- Any "explain", "I don't get it", "make a diagram", "show me" request in EE, Digital Electronics, Computer Engineering, or Calculus/maths.
- Default for study and homework help unless he asks for an explainer-notes HTML page (then use that skill instead).

## How to draw it
1. Silently call `mcp__visualize__read_me` with `modules: ["diagram"]` (add `"interactive"` only if a slider/stepper really helps). Never mention this call.
2. Call `mcp__visualize__show_widget` with ONE raw `<svg>` (viewBox `0 0 680 H`, `role="img"`, `<title>`, `<desc>`).
3. If the Visualizer is not available, build the same SVG as a small self-contained HTML Artifact.

### The look (keep it identical across topics)
- **Worked example with real numbers**, not a generic picture. Show the actual working, row by row, top to bottom, like doing it on paper.
- **Rows**: label on the left (`th` class, x=40), values in cells in the middle, a short note on the right (`ts` class, "= 5").
- **Cells**: 44 x 34 boxes, `rx=4`, 6px gaps, text centred with `dominant-baseline="central"`.
- **Column headers** above the cells when place value matters (8 4 2 1, powers of 10, time steps).
- **Rule lines** (1px, `var(--border-strong)`) under the rows being added/combined, like a sum on paper.
- **Colour means something, only three colours:**
  - `c-gray` = given inputs / ordinary values
  - `c-amber` = the ONE thing that moves or matters (carry, the flipped bit, the changing term, the tangent point). Use amber connector arrows (`stroke="#BA7517"`) to show where it goes.
  - `c-teal` = the final result
- **Arrows** only for things that move (carry looping round, signal flow, substitution). Route with L-shaped paths so they never cross a box or label.
- No titles or paragraphs inside the SVG. Sentence case. 14px and 12px text only.
- Run the read_me viewBox checklist: nothing outside 680 wide, height = lowest element + ~30.

## Recipes by subject
- **Number systems / arithmetic (DE, CE)**: bit-cell rows, place-value headers, carry/borrow in amber with a loop arrow, result row in teal. (1's/2's complement, overflow, BCD, hex.)
- **Boolean / logic (DE)**: truth table as a cell grid with the output column teal and the row being discussed amber; K-maps as a 2x2 or 4x4 grid with Gray-code headers and group outlines (rounded rect, amber stroke, no fill); gate circuits as drawn gate symbols with labelled wires.
- **Timing / sequential (DE, CE)**: clock and signals as stepped waveforms on a shared time axis, the active edge marked amber, a dashed line down through all signals at that edge.
- **Circuits (EE)**: proper drawn schematic (resistor zig-zag, labelled sources, node dots, current arrows), never block diagrams or ASCII. Put values on components; put the node/loop being solved in amber; answer box teal.
- **Datapaths / memory / pipelines (CE)**: row of stage boxes left to right, the instruction or data word moving through in amber, one row per clock cycle.
- **Calculus / maths**: axes with a plotted curve (polyline, 0.5-1.5px), the key point or tangent line or shaded area in amber, the numeric answer in a teal box; for algebra/integration steps, use the row layout with the term that changes each line highlighted amber.

## What to write around it
Order, all short:
1. One sentence saying what the amber bit is and why it matters.
2. **Steps**: 2-4 numbered lines, each one action with the real numbers.
3. **Quick rule**: 1-2 bullet lines he can memorise.
4. **Check question**: one question with new numbers that uses the same idea. Don't give the answer.

Do not repeat the diagram's contents in prose. No long intros, no recaps.

## If he says he still doesn't get it
Draw a second, smaller diagram that zooms into the one confusing step (e.g. just the single column where the carry appears), with prose between the two diagrams. Never add more text instead of a picture.