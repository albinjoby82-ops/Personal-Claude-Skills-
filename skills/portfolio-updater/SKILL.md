---
name: "portfolio-updater"
description: "Update Albin's portfolio site (myportfolio.albinjoby82.workers.dev): add or edit projects, timeline, On the bench, roles and CV, then build and push."
category: tools
tags: [portfolio, website, nextjs, cloudflare, cv]
---

# Portfolio updater

The site is a Next.js app deployed on Cloudflare Workers, with source on GitHub (account albinjoby82-ops). Pages: Projects (home), Timeline, per-project pages under /projects/<slug>/, and a CV PDF at /albin-joby-cv.pdf.

## 1. Get the source
- Attach the portfolio repo from albinjoby82-ops with push access and clone it. If the repo name is unclear, ask Albin once.
- Find where content lives (a data/content file or MDX for projects, timeline entries, the hero, and the On the bench block). Edit content there, never hard-code it into components.

## 2. Work out the change
Albin usually describes updates in a sentence or two. Turn that into concrete edits. Common ones:
- **New project**: add an entry with the same fields as existing ones: number, category (Robotics, Hardware, Electronics, Events, Software), status (In progress, To-do, Hackathon, or finished), date range, title, one or two sentence summary, roles, tags/tools, slug, and a project page.
- **Project update**: change status, dates, summary, photos, or add results (e.g. team and participant numbers).
- **Roles**: add, end or change a role. Ended roles keep their dates, they are not deleted.
- **On the bench**: Right now, Learning, Tools, Where.
- **Hero line**: year of study and headline.
- **Timeline**: add a dated entry for anything new.
- Renumber projects if the order changes, and update the "N things I've made" count.

## 3. Writing rules
- Match the existing voice: first person, plain, specific, short. No buzzwords.
- Only use facts Albin gave. If a number, date or outcome is missing, ask instead of inventing it.
- Keep summaries to one or two sentences.

## 4. Consistency check
Before building, scan the whole site for anything the change makes stale or wrong:
- Year of study, current roles, and project statuses.
- The same project under two names.
- Placeholder links (e.g. href="#") and "photo" placeholders.
- Whether the CV PDF still matches the site. If not, tell Albin what differs and offer to update the CV.
List what you found in one short message and fix only what he approves.

## 5. Build, preview, ship
- Install dependencies and run the build. Fix any errors.
- Show Albin a short before/after summary of what changed (not the full diff).
- After he confirms, commit and push using the push-clean skill so commits are under his name with no Claude attribution. Pushing to main triggers the Cloudflare deploy.
- Once deployed, fetch the live page and confirm the change is there.

## Output
Keep replies short: what changed, anything flagged, and the live link once it's up.