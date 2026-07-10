// Friendly Floaty — foam collar (flooded-reserve primary buoyancy)
// The part that keeps a FLOODED unit afloat (RELIABILITY.md §4: 2 collars = ~160 cm^3
// closed-cell EVA/EPE -> +27.5% flooded reserve). NOT 3D-printed: this model is the
// CUT MASTER for EVA sheet stacking/heat-forming (print once as a template if useful).
// Axes: X = bottle long axis. Payload channel W70(Y) x H40(Z), centered 4 mm low so the
// bracket tray + cell holder pass through; the keel passes under via the channel.
include <params.scad>

module _rrect(w_z, w_y, r) {
    // rounded rect in the local XY plane of the rotated frame:
    // local x -> global -Z (height w_z), local y -> global Y (width w_y)
    hull() for (x = [-w_z/2 + r, w_z/2 - r]) for (y = [-w_y/2 + r, w_y/2 - r])
        translate([x, y]) circle(r = r, $fn = 32);
}

module foam_collar() {
    rotate([0, 90, 0]) difference() {
        cylinder(h = collar_t, d = foam_od, center = true, $fn = 96);
        // payload channel, centered 4 mm below the bottle axis (local +x = global -Z)
        translate([4, 0, 0])
            linear_extrude(collar_t + 2, center = true)
                _rrect(foam_bore_w, foam_bore_l, 6);
    }
}

foam_collar();
