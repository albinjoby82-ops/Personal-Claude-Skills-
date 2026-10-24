---
name: explain-stuff
description: Explain any concept in EE, DE, CE, maths or solid state in plain chat, with bold step headings, display LaTeX maths and a predict-first check question, plus one clean worked diagram when the idea is visual, when he asks, or when he is lost. Use whenever Albin asks to explain, break down, show or diagram something.
category: study
tags: [explain, worked-diagram, formulas, chat-format, check-questions, ee, de, ce, calculus]
---

# Explain stuff

This skill combines the old `explain-stuff` and `worked-diagram` skills. Albin is dyslexic and dislikes long text. He learns best from the working laid out step by step, with a clear picture when a picture helps. So every explanation is **a plain chat answer, plus one worked diagram when it earns its place, then a check question.**

## The shape of an answer

1. **One sentence** saying what we are finding, in plain words. No formula yet.
2. **The diagram**, if one is needed (see "When to draw"). It goes right after the sentence so the steps can point at it.
3. **Bold step headings**, one per step: `**Step 1: Convert the shape to cm**`. Under each, one or two short sentences, then the maths.
4. **Real numbers** as soon as the formula has been shown. One line per substitution, units kept. Small tables for lists of values.
5. **Check question** at the end: new numbers, same idea. He predicts first. Do not give the answer.

No intros, recaps or "key takeaways". Text complements the diagram and never repeats what it already shows.

## Maths and text style

- Display maths on its own line (`$$ ... $$`) with a blank line above and below. Never put a key formula inside a sentence.
- Real fractions, proper subscripts. Never ASCII maths like `R2/(R1+R2)`.
- **Never underscore notation** (w_p, N_D, E_C) in text. He doesn't understand it. Use LaTeX (`$N_D$`) or Unicode (μₙ, nᵢ).
- Name each symbol the first time it appears, in a few words with units, right under the formula. Never define a symbol twice.
- Use the course's own constants and graph values when he gives them. If you have to assume one, say which.
- Sentences under about 15 words, one idea each. Define a term the first time. Bold only headings and the one thing to remember.

## When to draw

Draw one diagram when any of these is true:

1. He asks ("draw it", "diagram", "show me", "make it interactive", "formula card").
2. The idea is spatial or has working laid out in rows: number systems, circuits, waveforms, graphs, K-maps, lattices, carriers moving in a bar.
3. He says he is lost and the chat steps did not land.

Otherwise stay in plain chat. A diagram that restates a simple formula only adds clutter.

## How to draw it

1. Silently call `mcp__visualize__read_me` with `modules: ["diagram"]` (add `"interactive"` only if a slider or stepper really helps). Never mention this call.
2. Call `mcp__visualize__show_widget` with ONE raw `<svg>` (viewBox `0 0 680 H`, `role="img"`, `<title>`, `<desc>`).
3. If the Visualizer is not available, build the same SVG as a small self-contained HTML artifact.
4. Check the read_me viewBox list: nothing outside 680 wide, height = lowest element + about 30.

### The look (identical across topics)

- **Worked example with real numbers**, not a generic picture. Show the working row by row, top to bottom, like doing it on paper.
- **Rows**: label on the left (`th`, x=40), values in cells in the middle, a short note on the right (`ts`).
- **Cells**: 44 x 34 boxes, `rx=4`, 6px gaps, text centred with `dominant-baseline="central"`. Column headers above when place value matters (8 4 2 1, powers of 10, time steps).
- **Rule lines** (1px) under rows being added or combined.
- **Three colours, each with one meaning:**
  - `c-gray` = given inputs and ordinary values
  - `c-amber` = the ONE thing that moves or matters (carry, flipped bit, changing term, tangent point, the carriers). Amber connector arrows (`stroke="#BA7517"`) show where it goes.
  - `c-teal` = the final result
- **Arrows** only for things that move (carry, signal flow, substitution, diffusion). Route with L-shaped paths so they never cross a box or label.
- Label every arrow in words next to it ("diffusion: electrons spread right"), so colour is never the only signal.
- No titles or paragraphs inside the SVG. Sentence case. 14px and 12px text only.

## Recipes by subject

- **Number systems and arithmetic (DE, CE)**: bit-cell rows, place-value headers, carry or borrow in amber with a loop arrow, result row teal.
- **Boolean and logic (DE)**: truth table as a cell grid (output column teal, discussed row amber). K-maps as a 2x2 or 4x4 grid with Gray-code headers and rounded amber group outlines. Gates as drawn symbols with labelled wires.
- **Timing and sequential (DE, CE)**: stepped waveforms on a shared time axis, active edge amber, a dashed line through all signals at that edge.
- **Circuits (EE)**: a proper drawn schematic (resistor zig-zag, labelled sources, node dots, current arrows), never block diagrams or ASCII. Values on components, the node or loop being solved in amber, answer box teal.
- **Datapaths, memory, pipelines (CE)**: stage boxes left to right, the instruction or data word moving through in amber, one row per clock cycle.
- **Calculus and maths**: axes with a plotted curve, key point or tangent or shaded area amber, numeric answer in a teal box. For algebra steps, use the row layout with the term that changes each line amber.
- **Semiconductors (SSD)**: a bar with dots whose density shows concentration (many on the left, few on the right), then one arrow per effect, each labelled: diffusion, drift needed, field E. Remember electrons move against E. Lattice pictures show the donor or the thermal pair in amber.

## If he says he doesn't get it

- **"I don't understand at all"**: do not repeat the same steps. Change the angle. Retell it as a short story or everyday analogy (a crowd spreading into an empty corridor), add one small diagram of the confusing part, then ask ONE question: which numbered line lost him.
- **He points at one line** ("how do we know this?"): answer only that line. Give the evidence from the numbers in the question, then check it a second way (for example with the equation). Keep it short.
- **"It's too much"**: cut to one sentence, the steps with maths, the check question. Drop tables and extras first. Never fix confusion by adding words, add a picture or a simpler example.

## Other formats

- Full HTML notes page: use `explainer-notes`.
- Formula card, only if asked: one formula big and centred in a white card (serif maths face, 34 to 48px), colour = meaning, a short "where" legend under it (chip, symbol, meaning, units).
- Interactive widget, only if asked or a slider truly helps: real buttons or inputs, 44px minimum, labelled in plain words, nothing animates by itself.

## Check question

One question with new numbers using the same idea. He predicts before anything is shown. When he answers, show the formula with the numbers substituted, then one line on why.

End with the check question. No recap.
