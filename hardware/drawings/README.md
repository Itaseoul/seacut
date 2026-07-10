# Drawings

Dimensioned assembly drawings (PDF) and 2D cut files (DXF) go here.

- `*.pdf` — dimensioned assembly / exploded views for makers who build by hand
- `*.dxf` — 2D profiles for laser cutting or CNC (if you make a non-bottle housing)

Generate from the CAD sources:

```
# 2D projection to DXF from an OpenSCAD part (add a projection() view, then)
openscad --export-format=dxf -o part.dxf part_2d.scad
```

For dimensioned PDF drawings, import the STEP into FreeCAD's TechDraw workbench and export to PDF, or annotate the assembly render. Keep the editable source alongside any PDF (OSHWA prefers editable originals over output-only formats).
