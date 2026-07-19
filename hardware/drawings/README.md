# Drawings

Dimensioned assembly drawings (PDF) and 2D cut files (DXF) go here.

- `*.pdf` — dimensioned assembly / exploded views for makers who build by hand
- `*.dxf` — 2D profiles for laser cutting or CNC (if you make a non-bottle housing)

Generate from the CAD sources:

```
# 2D projection to DXF from an OpenSCAD part (add a projection() view, then)
openscad --export-format=dxf -o part.dxf part_2d.scad
```

For dimensioned PDF drawings: the CAD is OpenSCAD (mesh-based CSG), so there is **no true STEP** to import ([../cad/README.md](../cad/README.md) → "About STEP"). Either import the STL/3MF into FreeCAD (mesh, lossy) and dimension it in the TechDraw workbench, or annotate the assembly render directly. Keep the editable `.scad` source alongside any PDF (OSHWA prefers editable originals over output-only formats).
