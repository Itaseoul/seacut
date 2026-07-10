// SEA:CUT / Friendly Floatee — electronics bracket
// Holds the LILYGO T-A7670G board and the 18650 cell, self-locating in the bottle.
// Axes: X = bottle long axis, +Z = up (antenna side), -Z = belly.
include <params.scad>

module cell_holder() {
    // C-channel snap holder for one 18650, along X, opening up
    difference() {
        rotate([0, 90, 0]) cylinder(h = cell_l, r = cell_d/2 + wall, center = true);
        rotate([0, 90, 0]) cylinder(h = cell_l + 2, r = cell_d/2 + clr, center = true);
        translate([-cell_l/2 - 1, -(cell_d/2 + wall + 1), 2])
            cube([cell_l + 2, cell_d + 2*wall + 2, cell_d]);
    }
}

module electronics_bracket() {
    bl = board_l + 2*wall + 2*clr;
    bw = board_w + 2*wall + 2*clr;
    ft = 1.6;
    union() {
        // open board tray
        difference() {
            translate([-bl/2, -bw/2, 0]) cube([bl, bw, ft + board_h]);
            translate([-bl/2 + wall, -bw/2 + wall, ft])
                cube([bl - 2*wall, bw - 2*wall, board_h + 1]);
            // zip-tie slots
            for (x = [-bl*0.28, bl*0.28])
                translate([x - 1.5, -bw/2 - 1, -1]) cube([3, bw + 2, ft + 1.2]);
        }
        // battery holder under the tray
        translate([0, 0, -cell_d/2 - 1]) cell_holder();
        // two curved locating ribs to seat in the bottle wall
        for (x = [-bl*0.35, bl*0.35])
            intersection() {
                translate([x - 2, -bottle_r + 2, -bottle_r]) cube([4, 2*bottle_r - 4, bottle_r + ft]);
                rotate([0, 90, 0]) cylinder(h = bl*2, r = bottle_r - clr, center = true, $fn = 120);
            }
    }
}

electronics_bracket();
