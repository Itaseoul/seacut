// SEA:CUT / Friendly Floatee drifter — shared parameters (mm)
// Hardware: CERN-OHL-P. Docs: CC BY 4.0. Firmware: MIT.
// MEASURE YOUR OWN BOTTLE and edit these. Defaults approximate a 1 L round PET bottle.

// --- bottle (upcycled PET) ---
bottle_id = 90;            // bottle inner diameter
bottle_r  = bottle_id / 2; // derived inner radius

// --- printing ---
wall = 2.4;                // printed wall thickness
clr  = 0.4;                // fit clearance
$fn  = 64;                 // curve smoothness

// --- LILYGO T-A7670G board (approximate, incl. headers) ---
board_l = 68;
board_w = 34;
board_h = 12;

// --- 18650 protected cell ---
cell_d = 18.6;
cell_l = 68;

// --- lead-free ballast pocket (self-righting weight) ---
ballast_l = 55;
ballast_w = 22;
