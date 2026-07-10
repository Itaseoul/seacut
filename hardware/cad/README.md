# CAD — printed inserts (parametric OpenSCAD)

The housing is an upcycled PET bottle, so only three small printed inserts are needed. All parts are parametric OpenSCAD: open `params.scad`, set your measured bottle inner diameter and board/cell sizes, and everything updates.

| File | Part | Role |
|---|---|---|
| `params.scad` | shared parameters | measure your bottle and edit here first |
| `electronics_bracket.scad` | electronics bracket | holds board + 18650, self-locates on the bottle wall |
| `ballast_keel.scad` | ballast keel | carries lead-free weight at the belly for self-righting |
| `recovery_loop.scad` | recovery loop | smooth closed loop for pole/net recovery, wildlife-safe |
| `assembly.scad` | assembly preview | all three parts inside a ghost bottle |

## Edit and export

Install OpenSCAD (free, open source). Open a part, edit `params.scad`, then export.

```
# STL (3D print, and GitHub renders STL in-browser)
openscad -o electronics_bracket.stl electronics_bracket.scad
# STEP (universal CAD interchange, editable in FreeCAD/Fusion/etc.)  [OpenSCAD 2024+]
openscad --export-format=step -o electronics_bracket.step electronics_bracket.scad
# assembly preview image
openscad -o assembly.png --autocenter --viewall --imgsize=1400,1000 assembly.scad
```

The committed `.stl` files are reference geometry. This is a starting point: measure your bottle, adjust `params.scad`, reprint. Prefer FreeCAD instead? Import the STEP and edit there; keep the OpenSCAD source as the parametric master (OSHWA prefers editable originals over output-only formats).

Units are millimeters. Print in a durable, non-toxic filament (PETG recommended for water contact); no supports needed for these shapes if oriented flat.
