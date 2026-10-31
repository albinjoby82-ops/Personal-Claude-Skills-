# onshape-part-builder

A Claude skill: describe a 3D-printed part in plain words, get back an Onshape-editable model, step by step.

- Asks only the questions that change the design (max 4 at a time)
- Agrees a feature plan + variables table first (written the way Onshape thinks)
- Builds in build123d stage by stage with a 4-view preview each stage
- Print-checks (overhangs, walls, clearances), then delivers STEP, STL, 3MF, DXF per sketch, a preview and an **Onshape rebuild sheet**
- Optional: direct build through the Onshape MCP, or a FeatureScript custom feature for part families

Files: `SKILL.md` (the skill — self-contained, script included), `scripts/cad_run.py`, `references/` (build123d cheatsheet, FDM rules, Onshape routes, rebuild-sheet template, related work), `evals/` (test prompts).

Install in Claude Code: copy this folder to `~/.claude/skills/onshape-part-builder`. In claude.ai: upload `SKILL.md` as a skill.
