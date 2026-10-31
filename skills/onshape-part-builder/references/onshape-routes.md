# Onshape routes B and C, and STEP import tips

## Route B — direct build through the Onshape MCP (hedless/onshape-mcp)

Open-source MCP server wrapping Onshape's REST API: 35 tools for documents, Part Studios, sketches (rectangle, circle, line, arc, polygon on Front/Top/Right planes), extrude/revolve/thicken/fillet/chamfer/boolean/pattern, variable table, FeatureScript evaluation, assemblies and mates, export to STL/STEP/Parasolid/GLTF. Repo: https://github.com/hedless/onshape-mcp

One-time setup on Albin's laptop (Claude Desktop or Claude Code, not claude.ai web):
1. Onshape → Developer Portal (https://dev-portal.onshape.com) → API keys → create → copy access + secret key.
2. `git clone https://github.com/hedless/onshape-mcp && cd onshape-mcp && python -m venv venv && source venv/bin/activate && pip install -e .`
3. Add to `~/.claude/mcp.json` (Claude Code) or `claude_desktop_config.json` (Claude Desktop):
```json
{"mcpServers": {"onshape": {"command": "/abs/path/onshape-mcp/venv/bin/python",
  "args": ["-m", "onshape_mcp.server"],
  "env": {"ONSHAPE_ACCESS_KEY": "…", "ONSHAPE_SECRET_KEY": "…"}}}}
```
4. Restart; test with "list my Onshape documents".

How to use it in this workflow:
- Make the feature plan (SKILL.md step 2) exactly as usual. Then execute it: `set_variable` for every variable first, then `create_sketch_*` + `create_extrude` per feature, in order, with `variableDepth`/`variableWidth` pointing at the variables so the tree is parametric.
- **Units: the server's sketch/extrude parameters are in inches.** Convert: mm / 25.4. Variables can be set with units ("2.4 mm"). Double-check the first feature in Onshape before continuing.
- Sketches on faces of earlier features were still "in research" in the server at the time of writing; if a sketch must sit on a face, use an offset standard plane instead, or build that feature in build123d and import the STEP for that piece.
- After each 1–2 features, ask him to glance at the Part Studio (that is the live preview on this route), or `export_part_studio` to STL and render a preview with cad_run.py's view code.
- Still deliver STL/3MF and the rebuild sheet (the sheet is now just documentation of what's in the tree).

## Route C — FeatureScript custom feature

Best when the part is a family (parametric by nature) or he wants a reusable tool. The result is a feature with a dialog: change `motorCount` or `boreDiameter` and the part regenerates. Onshape's own guidance: LLMs are already decent at FeatureScript because it's openly documented, but **always validate** in a Feature Studio; expect a couple of error round-trips.

Onshape Labs ships an official **FeatureScript MCP Server** (enable Onshape Labs in Account Preferences; see https://www.onshape.com/en/blog/get-started-featurescript-mcp-server). It lets Claude look up the FeatureScript standard library and test code against Onshape. Without it, Claude writes the `.fs` from knowledge and Albin pastes it in.

Workflow:
1. Plan the part as usual, but write the variables table as the feature's **parameters** (name, type, default, min/max).
2. Write `<name>.fs`. Skeleton:
```javascript
FeatureScript 2716;                       // use the version shown in a new Feature Studio
import(path : "onshape/std/common.fs", version : "2716.0");

annotation { "Feature Type Name" : "Motor Mount" }
export const motorMount = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Plate length" }
        isLength(definition.length, { (millimeter) : [20, 60, 300] } as LengthBoundSpec);
        annotation { "Name" : "Wall thickness" }
        isLength(definition.wall, { (millimeter) : [1.2, 2.4, 6] } as LengthBoundSpec);
        annotation { "Name" : "Hole count" }
        isInteger(definition.holes, { (unitless) : [1, 4, 12] } as IntegerBoundSpec);
    }
    {
        // 1. sketch on Top plane
        var sk = newSketch(context, id + "sk1", { "sketchPlane" : qCreatedBy(makeId("Top"), EntityType.FACE) });
        skRectangle(sk, "rect", { "firstCorner" : vector(-definition.length/2, -20*millimeter),
                                  "secondCorner" : vector(definition.length/2, 20*millimeter) });
        skSolve(sk);
        // 2. extrude
        opExtrude(context, id + "ex1", {
            "entities" : qSketchRegion(id + "sk1"),
            "direction" : evOwnerSketchPlane(context, { "entity" : qSketchRegion(id + "sk1") }).normal,
            "endBound" : BoundingType.BLIND, "endDepth" : definition.wall });
        // 3. holes: loop with definition.holes, opExtrude with operationType REMOVE, or opBoolean
    });
```
3. Paste-in instructions for him: Feature Studio (+ tab → Feature Studio) → paste → Commit → in the Part Studio, custom-features icon → pick the feature → fill the dialog.
4. Mirror the same geometry in build123d for the preview/STL so he sees it before pasting, and so the print files exist even if the .fs needs a fix.
5. If he reports an error, ask for the exact message line; typical ones are unit mismatches (every length needs `* millimeter`), a missing `skSolve`, or a query that matched nothing.

Reference: FeatureScript docs https://cad.onshape.com/FsDoc/ ; standard library source is readable from any Feature Studio (Onshape → std).

## Route A tips — STEP import and direct editing

- Onshape: Documents page → Create → Import → the `.step`. It lands as a Part Studio with one feature ("Import"). No tree.
- He can still change it with direct-editing features (Move face, Delete face, Modify fillet, Replace face, Offset surface) — each becomes a feature, so it's still parametric from there on. Good for nudging a hole or a wall; bad for rethinking the shape. For a rethink, use the rebuild sheet.
- DXFs: in a sketch on the plane named in the sheet, Insert DXF/DWG → mm → place at origin → extrude. This is the fast way to get the sketches exactly right without typing coordinates.
- STL/OBJ import gives a mesh: printable, not editable. Never send only an STL.
