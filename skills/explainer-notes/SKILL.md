---
name: explainer-notes
description: Make a single self-contained HTML explainer page in Albin's notes format (find/what's happening, drawn SVG diagrams, worked steps, check questions). Use for any topic, not just EE.
category: study
tags: [notes, html, diagrams, explainer, check-questions]
---

# Explainer notes (HTML)

Build one self-contained `.html` file that teaches a topic or works through a set of questions. Works for any subject: maths, physics, EE, coding, chemistry, history, etc.

The user is dyslexic. Short sentences, bold key numbers and words, tables over paragraphs. Never write walls of text.

## Workflow

1. **Read the source first.** If there is a sheet, PDF or slides, read it (pdftotext or render the page). Never describe a figure or question from memory.
2. **Get facts and numbers right before writing.** Compute every number in Python and keep the intermediate values to show in steps. Re-check against the source (e.g. formulas, given values).
3. **Draw diagrams as SVG files** in `diagrams/` (see Diagrams). Render each to PNG with cairosvg (`pip install --break-system-packages cairosvg`) and LOOK at it with Read. Fix overlapping or clipped labels before going on.
4. **Write `notes.md`** in the page format below.
5. **Build the HTML** with the build script below. It inlines every SVG and keeps `$$...$$` maths for MathJax, so the output is ONE file that still works when sent on its own.
6. **Check the HTML:** count `<svg` tags matches the diagrams, grep that key answers are present, and (if this is a variant of an earlier page) grep that no old values are left.
7. **Deliver** with SendUserFile, `display: render`, using the file name the user asked for. If they want to share it with others, offer to publish it as an artifact.

## Page format

```
# <Topic> — <Workings / Notes>
One context line (due date, module, source, student no. if relevant).

> callout for anything they must know first (assumptions, gaps in the sheet, AI-use declaration for homework)

---
## 0. Setup        (only if needed: given values, symbol mapping, definitions — as a table)

## <Section / Question>
**Find:** what we are trying to get, in plain words.
**What's happening:** the physical / real-world picture in 1–3 short sentences, before any formula.
![diagram](diagrams/<name>.svg)
> **Key idea:** the one rule this section uses (short, bulleted if 2+ parts). Define every new term in words.

**Step 1 — <short title>.**
- *Says:* what the equation says (only for non-obvious steps)
- *Why:* why it's true
$$equation with symbols$$
$$same equation with the real numbers = \mathbf{answer}$$

**Step 2 — ...**

| **<Answer name>** | **<value + unit>** |
|---|---|

✅ **Check:** one sanity check (other method, limiting case, sum adds up, sign/size makes sense).

<details><summary>🧠 <b>Try:</b> a short question that makes them think</summary>

Answer with the working, **bold result**.
</details>

---
## Final answers / Summary   (table matching the answer boxes or key takeaways)
```

Rules:
- Every section starts with **Find** and **What's happening** before any formula.
- Show real numbers next to symbols. Never invent shorthand symbols the source doesn't use; write the full fraction.
- At least one 🧠 check question per section, with the answer hidden in `<details>`. Leave a blank line after `<summary>` so markdown inside renders.
- Use ⚠️ callouts for assumptions or problems in the source (e.g. a symbol missing from the sheet), and say what was assumed.
- For non-maths topics, keep the same skeleton: Find → What's happening → diagram → Key idea → numbered steps/points → ✅ check → 🧠 Try.
- For homework, keep the AI-use declaration callout at the top.

## Diagrams

Proper drawn SVG schematics with clear labels, like a lab report. Never ASCII art or code-block diagrams.

- White background, rounded border, `viewBox` set, Segoe UI/Helvetica font.
- Colour-code: one colour per node/group/stage, and use the SAME colour in the text when referring to it. Palette: orange `#ea580c`, blue `#2563eb`, green `#16a34a`, purple `#7c3aed`, red `#dc2626` (arrows/currents/highlights), grey `#6b7280` (secondary values), ink `#1f2937`.
- Label each part with name in bold plus value in grey underneath.
- Draw only the part being discussed. Reduced/simplified versions get their own small diagram.
- Graphs: axes with ticks, the curve in blue, the answer point in red with dashed guide lines and a label.
- Write diagrams with a small Python helper class (line, wire/polyline, text, dot, polygon, arrow, plus domain symbols like resistor zig-zag, capacitor plates, sources, ground, or boxes/arrows for flowcharts). Add an x-offset `<g transform>` if left labels clip.
- Always render to PNG and look before building the page.

## Build script

Save as a scratch file and run from the folder containing `notes.md` and `diagrams/`. Change OUT to the requested file name.

```python
import re, markdown, html
SRC, OUT, TITLE = 'notes.md', 'notes.html', 'Notes'
src = open(SRC).read()
src = src.replace('<details>', '<details markdown="1">')
maths = []
def keep(m):
    maths.append(m.group(0)); return f'@@MATH{len(maths)-1}@@'
src = re.sub(r'\$\$.+?\$\$', keep, src, flags=re.S)
src = re.sub(r'!\[([^\]]*)\]\(([^)]+\.svg)\)', lambda m: f'<div class="fig">{open(m.group(2)).read()}</div>', src)
body = markdown.markdown(src, extensions=['tables', 'md_in_html', 'fenced_code'])
for i, m in enumerate(maths):
    body = body.replace(f'@@MATH{i}@@', html.escape(m, quote=False))
page = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title>
<script>window.MathJax={{tex:{{displayMath:[['$$','$$']]}}}};</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js"></script>
<style>
:root{{--bg:#f8fafc;--fg:#1f2937;--card:#fff;--line:#e5e7eb;--acc:#2563eb}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f172a;--fg:#e5e7eb;--card:#1e293b;--line:#334155;--acc:#60a5fa}}}}
body{{background:var(--bg);color:var(--fg);font:16px/1.55 "Segoe UI",Helvetica,Arial,sans-serif;max-width:860px;margin:0 auto;padding:16px}}
h1{{font-size:1.7em}} h2{{border-bottom:2px solid var(--acc);padding-bottom:4px;margin-top:2em}}
table{{border-collapse:collapse;margin:10px 0}} td,th{{border:1px solid var(--line);padding:6px 12px}}
blockquote{{background:var(--card);border-left:4px solid var(--acc);margin:12px 0;padding:8px 14px;border-radius:6px}}
details{{background:var(--card);border:1px dashed var(--acc);border-radius:8px;padding:8px 14px;margin:14px 0}}
summary{{cursor:pointer}} .fig svg{{max-width:100%;height:auto}} .fig{{margin:12px 0}}
code{{background:var(--card);padding:1px 5px;border-radius:4px}} hr{{border:0;border-top:1px solid var(--line)}}
mjx-container{{overflow-x:auto;overflow-y:hidden}}
</style></head><body>{body}</body></html>'''
open(OUT, 'w').write(page)
print(len(page))
```

Notes: needs `pip install --break-system-packages markdown` if missing. Diagrams keep a white background in dark mode on purpose so the schematics stay readable.

## Variants of an existing page

When asked to redo a page with different inputs (e.g. another student number or dataset): copy the folder, re-read the source formulas, recompute everything in Python, update diagram labels with exact-match replacements (assert each matches once), rewrite every number in the notes, and flag anything that changes character (e.g. a value turning negative) with a short callout explaining it. Then grep the output to confirm no old values remain.

## Finish

One line saying what the file is, then a small table of the key answers/takeaways, then any assumptions the user must check. No recap of steps.