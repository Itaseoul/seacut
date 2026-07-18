// Friendly Floaty — Tier 1.5 SOLAR VARIANT visual mockup (NOT printed parts)
// Wrap-around thin-film cells + COTS charge controller + Gore-Tex vent patch.
// ★This file EXPORTS NO PRINTABLE STL — like mockups.scad it is a visual stand-in.
//   Kernels held by construction: NO new printed part · ballast unchanged (40 g) ·
//   non-metal RF-transparent cells only (B5) · self-right preserved (T7).
// Axes match mockups.scad/assembly.scad: X = bottle long axis (+X = cap), +Z = up (antenna side).
//   The wrap uses the SAME rotate([0,90,0]) as bottle_mock, so local +z -> global +X and
//   local -x -> global +Z. The RF window is therefore cut around LOCAL -x so it lands on +Z.
//   ★If the film-free wedge ends up on the bottom, flip the window rotate (render to confirm).
include <params.scad>

// pie sector centered on +x, half-angle deg/2, radius r, height h (for the RF window cut)
module _sector(deg, r, h) {
    step = 4;
    pts = concat([[0, 0]], [for (a = [-deg/2 : step : deg/2]) [r*cos(a), r*sin(a)]]);
    linear_extrude(height = h, center = true) polygon(pts);
}

// one film band: thin annulus around local Z, with the top (+Z after parent rotate) sector removed
module solar_band(bw) {
    ro = solar_wrap_r + solar_film_t;
    difference() {
        difference() {
            cylinder(h = bw, r = ro, center = true, $fn = 96);
            cylinder(h = bw + 2, r = solar_wrap_r, center = true, $fn = 96);
        }
        // RF window on LOCAL -x  =>  GLOBAL +Z after the parent rotate([0,90,0])
        rotate([0, 0, 180]) _sector(solar_rf_deg, ro + 2, bw + 2);
    }
}

// the two bands wrapping the body (same rotate as bottle_mock: local +z -> global +X)
module solar_wrap() {
    rotate([0, 90, 0])
        for (bx = solar_band_x)
            translate([0, 0, bx]) solar_band(solar_band_w);
}

// COTS charge controller envelope — zip-tied to the EXISTING bracket rib (a mock, not a printed clip)
module solar_controller_mock() {
    cube([solar_ctrl_l, solar_ctrl_w, solar_ctrl_h], center = true);
}

// Gore-Tex ePTFE adhesive patch on the cap (+X) — NOT a printed boss
module solar_vent_patch() {
    cylinder(h = 0.5, d = solar_vent_patch_d, center = true, $fn = 48);
}

// --- wiring (viz only) — where the charge path physically runs ---
module _wire(p1, p2, d = 1.8) {
    hull() { translate(p1) sphere(d/2, $fn = 14); translate(p2) sphere(d/2, $fn = 14); }
}
// panel-in lead: controller -> resealed-seam grommet (existing penetration) -> onto the external film band
module solar_wire_panel() {
    ctrl = [solar_ctrl_x, board_w/2 + 3, solar_ctrl_z];
    _wire(ctrl, [solar_ctrl_x - 6, board_w/2 + 11, 9]);                 // up to the seam grommet
    _wire([solar_ctrl_x - 6, board_w/2 + 11, 9], [-39, solar_wrap_r - 3, 7]); // out onto the -X film band
}
// battery + NTC leads: controller -> 18650 can, and controller -> NTC bead bonded on the cell
module solar_wire_batt() {
    ctrl = [solar_ctrl_x, board_w/2 + 3, solar_ctrl_z];
    _wire(ctrl, [solar_ctrl_x, 8, -9]);
    _wire([solar_ctrl_x, 8, -9], [12, 6, -(cell_d/2 + 1) + 3]);         // charge lead to the 18650
    _wire(ctrl, [8, 10, -(cell_d/2 + 1) + 5]);                          // NTC sense lead
}
// NTC thermistor bead, epoxy-bonded to the 18650 can (low-temp charge cutoff)
module solar_ntc_mock() {
    translate([8, 6, -(cell_d/2 + 1) + 5]) cube([5, 4, 3], center = true);
}

// echo the estimated budget + the bench-replacement reminder (K4 honesty)
module solar_report() {
    echo(str("[SOLAR] added_mass_g(EST)=", solar_added_mass_g,
             "  foam_vol_solar=", foam_vol_solar, " cm3",
             "  collar_t_solar=", collar_t_solar, " mm",
             "  foam_coeff=", solar_foam_coeff, " cm3/10g",
             "  substrate=", solar_cell_substrate, " (metal => ABORT)"));
    echo("[SOLAR] ESTIMATES — replaced by bench G5(harvest) / T7(self-right w cells) / T1(soak w wiring) / T6(RF w cells).");
}

// standalone preview when opened directly (assembly.scad drives the real placement)
if ($preview && solar_enable) {
    color("MidnightBlue", 0.85) solar_wrap();
    solar_report();
}
