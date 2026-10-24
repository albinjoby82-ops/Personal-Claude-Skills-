---
name: explain-stuff
description: Explain any concept in plain chat, ChatGPT style, with bold step headings, display LaTeX maths on its own line, short text between steps, then a predict-first check question. Diagrams, formula cards and interactive widgets only when truly needed or asked for. Use whenever Albin asks to explain, teach or break down anything in EE, DE, CE, maths or any other topic.
category: study
tags: [explain, formulas, chat-format, interactive, check-questions]
---

# Explain stuff

**Default is plain chat.** Albin is dyslexic and dislikes long text and fancy layouts. He tried the tabbed formula-card widget and asked for the plain chat layout instead: bold step headings, big maths on its own line, short text in between.

Fancy visuals are the exception, not the default (see "When to use a diagram or widget").

## Default layout (in chat)

1. **One sentence** saying what we are finding, in plain words. No formula yet.
2. **Bold step headings**, one per step: `**Step 1: Convert the shape to cm**`.
3. Under each heading: one or two short sentences, then the maths.
4. **Real numbers** as soon as the formula has been shown. One line per substitution, units kept.
5. **Tables** for lists of values (samples, constants, results). Keep them small.
6. **Check question** at the end: new numbers, same idea, predict first. Do not give the answer.

No intros, recaps, "key takeaways", or depth switches.

## Maths

- Display maths on its own line: `$$ ... $$`, with a blank line above and below.
- Never put a key formula inside a sentence.
- Real fractions (`\frac{}{}`), proper subscripts, `\cdot`, `\sum`, `\oplus` as needed.
- Never ASCII maths like `R2/(R1+R2)`.
- **Never underscore notation** in text (w_p, N_D, E_C). Albin doesn't understand it. Use LaTeX (`$N_D$`) or Unicode subscripts (μₙ, μₚ, nᵢ).
- Name each symbol the first time it appears: a few words and the units, in one line or a small table right under the formula. Never define a symbol twice.
- Use the course's own constants and graph values when he gives them (his notes beat textbook values). If you don't have them, say which value you assumed.

## Text style

- Sentences under about 15 words. One idea each.
- Define a term the first time, in a few words.
- Bold only headings and the one thing he must remember.
- Never say in words what a diagram or table already shows.

## When to use a diagram or widget

Only when one of these is true:

1. **He asks for it**: "draw it", "diagram", "show me", "make it interactive", "formula card", "explainer page".
2. **The idea is spatial or dynamic and text can't carry it**: waveforms, band diagrams, circuits, K-maps, anything where seeing it is the point.

In case 2, still lead with the plain chat explanation. Add **one** small visual. Never replace the chat explanation with a widget.

If he is still lost after the chat explanation, a small diagram of the one confusing step is the fix. Don't add more words.

### How to draw it, when it is needed

- Circuit schematics, worked-example rows and other diagrams: follow the `worked-diagram` skill.
- Full HTML notes page: use `explainer-notes`.
- Interactive widget: `mcp__visualize__read_me` (module `interactive`, plus `diagram` if drawing), then ONE `show_widget`. Controls are real buttons or inputs, 44px minimum, labelled in plain words. Nothing animates by itself. Colour is never the only signal.

| Concept | Control |
|---|---|
| A value that changes an outcome (R2, frequency, step size) | slider with a live bar or plot beside it |
| Bits, logic inputs, switches | tap-to-flip cells that recompute the output |
| A 2 to 3 step derivation | small tabs that swap the formula |
| A prediction | buttons, answer reveals with the working |

### If he asks for a formula card

- One formula, big and centred, in a white card (serif maths face such as STIX Two Text, 34 to 48px).
- Colour = meaning. Each symbol keeps the same colour in the formula, legend and diagram (teal `#0f766e`, orange `#b45309`, blue `#1d4ed8`, purple `#6d28d9`; plain ink for constants).
- A short "where" legend right under it: colour chip, symbol, meaning, units.

## Check question

One question with new numbers using the same idea. Ask him to predict before showing anything. When he answers, show the formula with the numbers substituted, then one line on why.

## If he says it is too much

Cut to: one sentence, the steps with maths, the check question. Drop tables and extras first. Never fix confusion by adding words.

## Finish

End with the check question. No recap.
