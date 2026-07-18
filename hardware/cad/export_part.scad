// Friendly Floaty — per-part STL export in ASSEMBLED coordinates (for the web viewer)
//   openscad -o out/<name>.stl -D part="<name>" export_part.scad
// names: bracket keel loop foam_a foam_b board antennas cell ballast bottle
include <params.scad>
use <electronics_bracket.scad>
use <ballast_keel.scad>
use <recovery_loop.scad>
use <foam_collar.scad>
use <mockups.scad>

part = "bracket";

if (part == "bracket")       electronics_bracket();
else if (part == "keel")     ballast_keel();
else if (part == "loop")     translate([0, 0, bottle_r + 1]) recovery_loop();
else if (part == "foam_a")   translate([ collar_x, 0, 0]) foam_collar(solar_enable ? collar_t_solar : collar_t);
else if (part == "foam_b")   translate([-collar_x, 0, 0]) foam_collar(solar_enable ? collar_t_solar : collar_t);
else if (part == "board")    board_mock();
else if (part == "antennas") antennas_mock();
else if (part == "cell")     cell_mock();
else if (part == "ballast")  ballast_mock();
else if (part == "bottle")   bottle_mock();
