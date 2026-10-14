# Rules for adding skills to this repo

When asked to save or create a skill here, always do all of this:

1. **Name**: lowercase kebab-case, max 40 chars, says what it does (`exam-cram-notes`, `ltspice-helper`). Not vague (`helper`, `notes2`). Check `skills/` first so you never duplicate or clash with an existing name.
2. **Folder**: `skills/<name>/SKILL.md`. Folder name must equal the `name:` field. Extra files (scripts, templates) go inside the same folder.
3. **Frontmatter** (all four keys):
   ```
   ---
   name: <name>
   description: <one sentence, max 500 chars, say when to use it. No angle brackets.>
   category: <study|ee|kicad|git|writing|tools|other>
   tags: [a, b, c]
   ---
   ```
   `category` and `tags` are for this repo only. The Claude save card ignores them.
4. **Rebuild the index**: `python3 scripts/build_index.py`. It validates names and rewrites the table in README.md. Fix any ERROR lines.
5. **Commit and push**: `git add -A && git commit -m "Add <name> skill" && git push`. Never hand-edit the table between the INDEX markers.
6. Tell the user the skill name and category in one line.

Updating a skill: edit its SKILL.md, rerun the index script, commit and push.
Renaming a skill: rename the folder and `name:`, rerun the script, mention the old name in the commit message.
