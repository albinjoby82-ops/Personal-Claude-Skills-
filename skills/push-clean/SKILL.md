---
name: push-clean
description: Commit and push to GitHub under the user's own git identity with no Claude attribution (no Co-Authored-By trailer, no "Generated with Claude" line in commits or PRs). Use whenever the user says "push clean", "push without the Claude tag", "commit and push as me", "push without Claude credited", or asks to commit, push or open a PR without Claude listed as author or co-author, even if they don't name the skill.
category: git
tags: [git, github, commit, push, no-attribution]
---

# push-clean

Commit and push so the work is credited only to the user. GitHub lists Claude as a contributor when a commit message carries a trailer like `Co-Authored-By: Claude <noreply@anthropic.com>`. Leave the trailer out and the commit shows only the user's name.

## Steps

1. **Check identity.** Run `git config user.name` and `git config user.email`.
   - If the email is unset, set it for this repo: `git config user.email "albin@gaelforceucd.ie"`.
   - If the name is unset, ask the user what name to use. Don't guess.

2. **Review and stage.** Run `git status`. Stage what the user asked for (default `git add -A`). If anything looks like a secret (`.env`, keys, tokens), stop and ask first.

3. **Write a plain commit message.** One short imperative line (e.g. `Add ornament submission template`), plus a body only if needed. Use `git commit -m "..."`. Do not add a `Co-Authored-By` line, a "Generated with" line, or any mention of Claude or Anthropic.

4. **Check before pushing.** The commit is still local, so it's cheap to fix.
   - `git log -1 --format='%an <%ae>'` should show the user's name and email.
   - `git log @{u}..HEAD --format=%B | grep -iE 'co-authored-by|claude|anthropic'` (or `git log -5 --format=%B` if no upstream yet) should print nothing.
   - If a trailer appears, remove it with `git commit --amend` (or `git rebase -i` for several commits), then re-check. Only rewrite commits that haven't been pushed.

5. **Push.** `git push`, or `git push -u origin HEAD` if the branch has no upstream. Don't force-push unless the user explicitly says to. If cleaning requires rewriting commits that are already pushed, explain that and ask first.

6. **Pull requests.** If the user wants a PR (`gh pr create`), write the body in plain text with no "Generated with Claude" footer.

7. **Report back** in one or two lines: branch, short commit hash, author shown.

## Notes

- Claude Code may add the trailer by default. Writing the message yourself in step 3 avoids it. If it keeps appearing, tell the user they can set `"attribution": {"commit": "", "pr": ""}` in `.claude/settings.json` (older versions: `"includeCoAuthoredBy": false`).
- This only controls what appears in the user's own repos. Never edit git history in repos the user doesn't own.
