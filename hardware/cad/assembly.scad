// SEA:CUT / Friendly Floatee — assembly preview
// Shows the three printed parts positioned inside a ghosted bottle.
// Render preview: openscad -o assembly.png --autocenter --viewall --imgsize=1400,1000 assembly.scad
include <params.scad>
use <electronics_bracket.scad>
use <ballast_keel.scad>
use <recovery_loop.scad>

// ghost bottle (background modifier, not part of geometry)
%rotate([0, 90, 0]) cylinder(h = 180, r = bottle_r, center = true, $fn = 120);

color("SteelBlue")   electronics_bracket();
color("DimGray")     ballast_keel();
color("Orange")      translate([0, 0, bottle_r - 3]) recovery_loop();
