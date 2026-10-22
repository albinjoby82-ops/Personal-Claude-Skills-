---
name: explain-stuff
description: Explain any concept with clean LaTeX-style formula cards, short text that complements a diagram, and light interactivity (tabs, sliders, tap-to-flip bits, predict-first check). Use whenever Albin asks to explain, teach or break down anything in EE, DE, CE, maths or any other topic.
category: study
tags: [explain, formulas, diagrams, interactive, ui, check-questions]
---

# Explain stuff

The diagram does the heavy lifting. The text only does three jobs: say the idea, show the formula cleanly, and name every symbol. Albin is dyslexic and dislikes long text, so **less is better**: if a line does not help him understand, cut it.

Use together with `worked-diagram` (it sets how the diagram itself is drawn). This skill sets the layout around it, the formulas, and the interactivity. If he asks for a full HTML notes page, use `explainer-notes` instead.

## Layout (always this order, nothing extra)

1. **Idea**: one sentence, plain words, no formula.
2. **Formula card**: the key formula, big and centred (see below).
3. **Diagram**: next to or directly under the formula, colours matching it.
4. **Caption**: one line under the formula saying what it means.
5. **Check**: one question, predict first, answer hidden until he commits.

No intros, recaps, depth switches, step lists repeated in prose, or "key takeaways" sections. If there are 2-3 steps, make them small tabs that swap the formula and highlight the matching part of the diagram, not paragraphs.

## Formula card

- Display maths only, on its own line: `$$ ... $$`, centred, with a blank line above and below. Never inline a key formula in a sentence.
- Real fractions (`\frac{}{}`), proper subscripts, `\cdot` / `\oplus` / `\sum` as needed. Never ASCII maths like `R2/(R1+R2)`.
- One formula per card. A chain (C1, then C2) is a short stack, one line each, aligned on the `=`.
- In HTML (Visualizer or artifact), set maths in a serif maths face (STIX Two Text), 34-48px, italic variables, subscripts at about 55%, fraction bar 2px. Card: white, 1px border, rounded, 24-48px padding.
- **Colour = meaning.** Each symbol keeps the same colour in the formula, legend and diagram. Palette: teal `#0f766e`, orange `#b45309`, blue `#1d4ed8`, purple `#6d28d9`; plain ink for given or constant things.
- **"where" legend** right under the formula: one short line per symbol (colour chip, symbol, meaning in a few words, units). Nothing else in it.
- When useful, one line of real numbers substituted in, same layout as the formula.

## Interactivity (only where it makes him think)

Use `mcp__visualize__read_me` (modules `interactive`, plus `diagram` if drawing) silently, then `show_widget` for ONE small widget. Pick the lightest control that fits:

| Concept | Control |
|---|---|
| A value that changes an outcome (R2, frequency, step size) | slider, with a live bar or plot beside it |
| Bits, logic inputs, switches | tap-to-flip cells, outputs recompute, add a check against the normal answer |
| A 2-3 step derivation | small tabs, each swapping the formula and dimming unrelated diagram parts |
| A prediction | buttons, answer reveals with the working |

Rules: controls are real buttons or inputs, 44px minimum, labelled in plain words; nothing animates by itself; colour is never the only signal. If the Visualizer is not available, build the same thing as a small self-contained HTML artifact.

## Text style

- Sentences under about 15 words. One idea each.
- Define a term the first time it appears, in a few words, never twice.
- Bold only the thing he must remember.
- Real numbers beat generic symbols once the formula has been shown.
- Never say what the diagram already shows.

## Check question

One question with new numbers using the same idea. Ask him to predict before showing anything. Reveal the answer as the formula with numbers substituted, then one line on why.

## If he says it is too much

Cut to: idea, formula card, diagram. Drop the legend, tabs and substitution line before dropping the diagram. Never fix confusion by adding words; add or zoom a diagram instead.

## Finish

End with the check question. No recap.
