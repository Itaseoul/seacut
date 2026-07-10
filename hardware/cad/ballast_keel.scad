// SEA:CUT / Friendly Floatee — ballast keel (self-righting)
// Seats at the belly (-Z) and carries lead-free weight low, so the float always
// rights itself antenna-up no matter how it rolls.
// Axes: X = bottle long axis, -Z = belly.
include <params.scad>

module ballast_keel() {
    Lx = ballast_l + 2*wall;
    Wy = ballast_w + 2*wall;
    Hz = bottle_r * 0.5;
    difference() {
        // slab at the belly, trimmed to the bottle inner wall
        intersection() {
            translate([-Lx/2, -Wy/2, -bottle_r]) cube([Lx, Wy, Hz]);
            rotate([0, 90, 0]) cylinder(h = Lx + 4, r = bottle_r - clr, center = true, $fn = 120);
        }
        // open weight pocket (pack with lead-free sinkers, then seal)
        translate([-ballast_l/2, -ballast_w/2, -bottle_r + wall]) cube([ballast_l, ballast_w, Hz]);
        // zip-tie / drain holes
        for (x = [-Lx*0.32, Lx*0.32])
            translate([x, 0, -bottle_r - 1]) cylinder(h = Hz + 2, r = 1.8, $fn = 24);
    }
}

ballast_keel();
