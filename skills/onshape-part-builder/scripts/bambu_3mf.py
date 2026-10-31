"""Bambu Studio 3MF writer: one object, named parts, filament slots preset.
usage: from bambu_3mf import bambu_3mf; bambu_3mf("out.3mf", "name", [("black", mesh, 1), ...])"""
import zipfile, numpy as np
def bambu_3mf(path, obj_name, parts, centre=(128, 128)):
    """parts: [(name, trimesh.Trimesh, filament_slot)] -> one object, named parts, slots preset."""
    allv = np.vstack([m.vertices for _, m, _ in parts]); lo, hi = allv.min(0), allv.max(0)
    off = np.array([centre[0]-(lo[0]+hi[0])/2, centre[1]-(lo[1]+hi[1])/2, -lo[2]])
    objs, comps, cfg = [], [], []
    for i, (n, m, slot) in enumerate(parts, 1):
        m = m.copy(); m.merge_vertices(); m.apply_translation(off)
        v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in m.vertices)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
        objs.append(f'<object id="{i}" type="model"><mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
        comps.append(f'<component objectid="{i}"/>')
        cfg.append(f'<part id="{i}" subtype="normal_part"><metadata key="name" value="{n}"/><metadata key="extruder" value="{slot}"/></part>')
    top = len(parts) + 1
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">'
             '<metadata name="Application">BambuStudio-01.10.00.00</metadata><metadata name="BambuStudio:3mfVersion">1</metadata><resources>'
             + "".join(objs) + f'<object id="{top}" type="model"><components>{"".join(comps)}</components></object></resources>'
             f'<build><item objectid="{top}" printable="1"/></build></model>')
    config = (f'<?xml version="1.0" encoding="UTF-8"?><config><object id="{top}"><metadata key="name" value="{obj_name}"/>'
              '<metadata key="extruder" value="1"/>' + "".join(cfg) + '</object></config>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '<Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model); z.writestr("Metadata/model_settings.config", config)
