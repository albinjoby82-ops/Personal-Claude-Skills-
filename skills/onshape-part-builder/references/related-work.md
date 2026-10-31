# Related repos, skills and write-ups this skill borrows from

Code-CAD with Claude (the approach route A uses)
- flowful-ai/cad-skill — https://github.com/flowful-ai/cad-skill — the most-used Claude Code CAD skill (CadQuery). Its ideas copied here: build in phases (base shape → features → finish), a subprocess runner that captures errors so Claude self-corrects, 6-view preview renders, a design-review checklist after every preview (shape matches request? bottom flat? overhangs < 45°? walls > 1.2 mm?). Write-up: "I Taught Claude to Design 3D-Printable Parts" — https://pub.towardsai.net/i-taught-claude-to-design-3d-printable-parts-heres-how-675f644af78a
- fingerskier/build123d-claude-plugin — https://github.com/fingerskier/build123d-claude-plugin — MCP server with execute/export_stl/export_step/render_image tools and a build123d API guide for Claude.
- JonFermin/cadsmith — https://github.com/JonFermin/cadsmith — make-model / edit-model / export-model skills plus a Three.js browser preview.
- clawd-maf/cad-agent — https://github.com/clawd-maf/cad-agent — build123d rendering server in Docker.
- aradotso text-to-cad-harness — https://claudemarketplaces.com/skills/aradotso/trending-skills/text-to-cad-harness
- fboldo/openscad-mcp-server — https://github.com/fboldo/openscad-mcp-server — OpenSCAD PNG/STL renderer with an "iterate and refine" skill. OpenSCAD cannot export STEP, so it is not used here.
- build123d docs — https://build123d.readthedocs.io ; CadQuery docs — https://cadquery.readthedocs.io

Onshape
- hedless/onshape-mcp — https://github.com/hedless/onshape-mcp — route B.
- Onshape FeatureScript MCP Server (Onshape Labs) — https://www.onshape.com/en/blog/get-started-featurescript-mcp-server and use-cases https://www.onshape.com/en/blog/featurescript-mcp-server-use-cases-text-code-cad — route C.
- FeatureScript docs — https://cad.onshape.com/FsDoc/
- Onshape forum thread on what people built with the FS MCP server — https://forum.onshape.com/discussion/31780/
- Onshape tech tip: importing and direct-editing STEP — https://www.onshape.com/en/resource-center/tech-tips/import-edit-step-iges-parasolid-stl

Other CAD MCPs (not used, for reference)
- FreeCAD MCP (neka-nat) — https://github.com/neka-nat/freecad-mcp — drives a live FreeCAD with a screenshot after each operation.
- Fusion 360 MCP servers (several, e.g. KevinZhao-07/Fusion-Mcp-Server) — drive a live Fusion session.
- Snyk's list of 9 CAD MCP servers — https://snyk.io/articles/9-mcp-servers-for-computer-aided-drafting-cad-with-ai

Lessons from users (HN thread https://news.ycombinator.com/item?id=48234090 and the write-ups above)
- Agree the base shape before details; whole-part one-shots waste work when the base is wrong.
- Clearances need a fit-test: one user dropped Claude's 0.3 mm to 0.1 mm for a perfect TPU fit.
- Models struggle with organic shapes and with vase-mode / snap-fit tolerances; brackets, mounts, adapters, enclosures and robotics parts are the sweet spot.
- Use real dimensions from datasheets or measurement; "about 50 mm" is how parts don't fit.

Albin's own related skills
- image-to-cad-dxf — picture → closed-loop DXF for a sketch (same DXF delivery idea used here for sketches).
- image-to-kicad-dxf — board outlines.
