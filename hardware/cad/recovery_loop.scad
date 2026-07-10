// SEA:CUT / Friendly Floatee — recovery loop
// A smooth closed loop for pole/net recovery. No sharp edges or open hooks, so it
// will not entangle wildlife or snag nets and propellers. Glue/screw to the top.
include <params.scad>

loop_r = 18;   // loop radius
loop_cs = 4;   // loop cross-section radius (smooth, rounded)
base_l = 30;
base_w = 16;
base_t = 3;

module torus(R, cs) rotate_extrude($fn = 72) translate([R, 0, 0]) circle(r = cs, $fn = 24);

module recovery_loop() {
    difference() {
        union() {
            // rounded base plate
            hull() for (x = [-base_l/2 + 4, base_l/2 - 4]) for (y = [-base_w/2 + 4, base_w/2 - 4])
                translate([x, y, 0]) cylinder(h = base_t, r = 4, $fn = 32);
            // upright smooth loop
            translate([0, 0, base_t + loop_r]) rotate([90, 0, 0]) torus(loop_r, loop_cs);
        }
        // mounting holes
        for (x = [-base_l/2 + 5, base_l/2 - 5])
            translate([x, 0, -1]) cylinder(h = base_t + 2, r = 1.8, $fn = 24);
    }
}

recovery_loop();
