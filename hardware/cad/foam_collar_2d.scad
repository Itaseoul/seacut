// Friendly Floaty — foam collar 2D CUT TEMPLATE (1:1, mm)
// Same source of truth as foam_collar.scad: the collar cross-section projected to 2D.
// Export:  openscad -o foam_collar_template.svg foam_collar_2d.scad     (print at 100%)
//          openscad -o foam_collar_template.dxf foam_collar_2d.scad     (laser/CNC)
// Orientation: +Y on this template = UP (antenna side) when inserted in the bottle.
// The payload channel sits 4 mm BELOW center — keep the arrow up when stacking.
include <params.scad>

module _rrect2(w, h, r) {
    hull() for (x = [-w/2 + r, w/2 - r]) for (y = [-h/2 + r, h/2 - r])
        translate([x, y]) circle(r = r, $fn = 32);
}

module foam_collar_profile() {
    difference() {
        circle(d = foam_od, $fn = 128);
        // channel: width 70 (X here = bottle Y), height 40, centered 4 mm low
        translate([0, -4]) _rrect2(foam_bore_l, foam_bore_w, 6);
    }
}

foam_collar_profile();

// UP arrow marker (kerf-thin, engrave/skip when knife-cutting)
translate([0, foam_od/2 - 6]) polygon([[0, 4], [-2.5, -2], [2.5, -2]]);
