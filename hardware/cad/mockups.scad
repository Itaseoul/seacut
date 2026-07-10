// Friendly Floaty — real-size visual mockups (NOT printed parts)
// Dimensional stand-ins for the full assembly view: bottle, LILYGO board, 18650,
// ballast pack, antennas. Sizes from params.scad / BOM; measure YOUR parts and adjust.
// Axes: X = bottle long axis (+X = cap/neck), +Z = up (antenna side).
include <params.scad>

module bottle_mock() {
    // thin shell so the viewer can look inside (visual wall 1 mm)
    x1 = bottle_body_x0 + bottle_body_l;                 // body end (+X)
    rotate([0, 90, 0]) translate([0, 0, 0]) union() {
        // body shell: local +z = global +X
        translate([0, 0, bottle_body_x0]) difference() {
            cylinder(h = bottle_body_l, d = bottle_id + 2, $fn = 96);
            translate([0, 0, -1]) cylinder(h = bottle_body_l + 2, d = bottle_id, $fn = 96);
        }
        // base cap (slightly domed, closed)
        translate([0, 0, bottle_body_x0 - 1]) cylinder(h = 2, d = bottle_id + 2, $fn = 96);
        // shoulder taper to neck
        translate([0, 0, x1]) difference() {
            cylinder(h = shoulder_l, d1 = bottle_id + 2, d2 = cap_d - 4, $fn = 96);
            translate([0, 0, -1]) cylinder(h = shoulder_l + 2, d1 = bottle_id, d2 = cap_d - 6, $fn = 96);
        }
        // neck + cap
        translate([0, 0, x1 + shoulder_l]) cylinder(h = neck_l, d = cap_d, $fn = 64);
    }
}

module board_mock() {
    // LILYGO T-A7670G R2: PCB + component block, sits in the bracket tray (floor z=1.6)
    union() {
        translate([-board_l/2, -board_w/2, 1.6]) cube([board_l, board_w, 1.6]);         // PCB
        translate([-board_l/2 + 4, -board_w/2 + 3, 3.2]) cube([board_l - 8, board_w - 6, board_h - 4]); // parts
    }
}

module antennas_mock() {
    // taped to the upper inner wall: LTE FPC stick + GNSS patch (visual)
    translate([-45, -6, 34]) cube([70, 12, 2]);           // LTE FPC
    translate([18, -12.5, 33]) cube([25, 25, 7]);         // GNSS patch
}

module cell_mock() {
    // protected 18650 in the C-holder under the tray (axis along X)
    translate([0, 0, -(cell_d/2 + 1)]) rotate([0, 90, 0])
        cylinder(h = cell_l, d = cell_d, center = true, $fn = 48);
}

module ballast_mock() {
    // lead-free weight pack filling the keel pocket (~40 g steel)
    translate([-ballast_l/2, -ballast_w/2, -bottle_r + wall])
        cube([ballast_l, ballast_w, 14]);
}
