---
name: exam-cram-notes
description: Build a diagram-heavy exam cram repo (slide snippet, explanation underneath, check question) from lecture slides, tutorials and past papers, then push it to GitHub.
category: study
tags: [exams, revision, notes, github, slides]
---

# Exam cram notes

Use when a student needs to understand ~70% of a module fast, with no lectures attended. Output is a GitHub repo of markdown notes, tests and mock exams. Keep chat replies short and to the point.

## The core loop (every idea in every note)

1. **Slide snippet**: a cropped image of the key slide/diagram.
2. **Explanation underneath**: a "How to read this diagram" bullet list, plain words, no waffle.
3. **Check question**: a short "Check" with the answer hidden in a `<details>` block.

Repeat for each idea so the student can confirm they have caught up before moving on.

Example shape (copy it):

```
![Fermi-Dirac](../img/05/s58.png)

**How to read this diagram:**
- x axis is energy, y axis is probability of a state being filled
- ...

### Check
What is the probability a state 0.1 eV above E_F is filled?

<details><summary>Answer</summary>
...
</details>
```

## Step 0: Setup

- Ask for (or find) the lecture slides, tutorial questions, official answers, formula sheet and any booklet. Tutorial questions drive the exam, so map everything to them.
- Create the repo folder with `git init`, then create a GitHub repo (`gh repo create <name> --public` or `--private`; ask which if unclear, and prefer private if course material is copyrighted).

## Step 1: Getting the slide snippets

- `pdftoppm -r 100 -png file.pdf out/` for pages. Build contact sheets with Pillow (grid with slide numbers) to find the diagram slides without reading every page.
- Crop the useful part at about 100 dpi, trim whitespace with Pillow.
- Save as `img/NN/sPAGE.png` for slides and `img/NN/ans-qX.png` for official answer figures (NN = topic number).
- Check each crop is not cut off before using it.

## Step 2: Triage into topics

- List the tutorial questions, then group them into topics in the order a beginner needs them. Skip junk that no tutorial question or formula-sheet item touches.
- Each topic: tutorial questions it covers, slide pages, equations.

## Step 3: Repo layout

```
README.md            conventions
TOPICS.md            tracker with links (tick only topics the student says are done)
formula-sheet.md     copy of the exam formula sheet
questions-asked.md   log of the student's confusion questions by topic
notes/NN-topic.md
questions/NN-topic.md
mock/midterm-1.md, midterm-2.md
img/NN/...
```

## Step 4: Notes structure (notes/NN-topic.md)

- Title, tutorial questions covered, slide pages.
- **The big idea**: 3 to 6 lines.
- Numbered sections, each following the core loop.
- **Equation boxes**: equation, symbol table with units, "What it means", "Use it when". Say whether it is on the formula sheet.
- **Worked example** from a real tutorial question, with the official answer image.
- **Drawing checklist** for any sketch the exam may ask.
- **Method table**: "You're asked for / Use".
- Link to the end-of-topic test.

## Step 5: Tests (questions/NN-topic.md)

- **Part A**: the tutorial questions with answers (and official answer images).
- **Part B**: M1 true/false, M2 multiple choice, M3 calculate, M4 sketch, M5 explain. Every answer cites the notes section.

## Step 6: Mock exams

- Two or more mocks built on the tutorial questions with changed numbers or a twist. Give marks, constants, a time guess, and answers in `<details>` blocks citing the notes sections.

## Step 7: Keeping the student oriented

- Use a task list for progress.
- Log every confusion question the student asks in `questions-asked.md` under its topic. Do not edit notes unless told to.
- Tick topics in `TOPICS.md` only when the student says they are done.

## Step 8: Final checks

- Recompute every number in Python.
- Run a link and image checker over all md files (no broken paths, details blocks balanced).
- Note unit traps and constant mismatches (e.g. two values of a constant) in the notes.

## Step 9: Commit and push to GitHub (always)

- Commit after each topic or batch, not just at the end: `git add -A && git commit -m "Add topic N notes and test" && git push`.
- Push all mock exams and any new files before finishing. Do not leave untracked files.
- Verify the push (e.g. `git status` clean and `git log origin/main..` empty, or check via `gh api`).
- Tell the student the repo link in one line, and warn if the repo is public and the material is copyrighted.
