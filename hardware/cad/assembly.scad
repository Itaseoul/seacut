// Friendly Floaty — FULL real-size assembly (printed parts + foam + electronics mocks)
// Renders the complete Tier-1 drifter as deployed: horizontal 1 L bottle, keel at the
// belly, board+cell in the bracket, 2 foam collars (flooded-reserve buoyancy),
// antennas up, recovery loop on top.
//
//   assembled : openscad -o assembly.png --autocenter --viewall --imgsize=1400,1000 assembly.scad
//   exploded  : openscad -o assembly_exploded.png -D explode=1 --autocenter --viewall --imgsize=1400,1000 assembly.scad
//
// Axes: X = bottle long axis (+X = cap), +Z = up (antenna side).
include <params.scad>
use <electronics_bracket.scad>
use <ballast_keel.scad>
use <recovery_loop.scad>
use <foam_collar.scad>
use <mockups.scad>
use <solar_variant.scad>

explode = 0;          // 0 = assembled, 1 = exploded (CLI: -D explode=1)
e = explode * 60;

// printed parts
color("SteelBlue")      translate([0, 0,  e * 0.30]) electronics_bracket();
color("DimGray")        translate([0, 0, -e * 0.80]) ballast_keel();
color("Orange")         translate([0, 0, bottle_r + 1 + e * 1.40]) recovery_loop();

// foam collars (cut from EVA sheet — flooded-reserve buoyancy, RELIABILITY §4)
color("Khaki")          translate([ collar_x + e * 1.2, 0, 0]) foam_collar();
color("Khaki")          translate([-collar_x - e * 1.2, 0, 0]) foam_collar();

// electronics / ballast mocks (real size)
color("ForestGreen")    translate([0, 0,  e * 0.90]) board_mock();
color("DarkSeaGreen")   translate([0, 0,  e * 1.15]) antennas_mock();
color("LightSlateGray") translate([0, 0, -e * 0.35]) cell_mock();
color("SlateGray")      translate([0, 0, -e * 1.20]) ballast_mock();

// bottle shell (translucent)
color("LightSkyBlue", 0.25) bottle_mock();

// --- Tier 1.5 SOLAR VARIANT overlay (render with -D solar_enable=1; default 0 = plain Tier 1) ---
// Wrap = adhesive film (no print) · controller = COTS on the bracket · vent = Gore-Tex patch.
// The RF window must sit over the antennas (+Z). Ballast/keel/loop/bracket are untouched (kernel #6).
if (solar_enable) {
    color("MidnightBlue", 0.85) solar_wrap();
    color("Gainsboro")
        translate([bottle_body_x0 + bottle_body_l + shoulder_l + neck_l - 2, 0, 0])
        rotate([0, 90, 0]) solar_vent_patch();                                  // cap end (+X)
    color("Firebrick")
        translate([solar_ctrl_x, board_w/2 + 3, solar_ctrl_z]) solar_controller_mock();
    solar_report();
    // ★For a real solar build also set  collar_t = collar_t_solar;  so both foam collars re-cut larger.
}
