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

// --- flotation & hydrostatics (NEW; estimates — verify per build; see hardware/RELIABILITY.md) ---
// Sealed 1 L bottle displaces ~1000 cm^3 -> reserve ratio ~4.83x (never sinks intact).
// Real failure = seal leak -> flooded net buoyancy ~ -97 gf -> sinks. Foam reverses it.
foam_vol             = 160;   // cm^3 closed-cell foam (flooded reserve; non-BOM NEW part)
foam_density         = 0.04;  // g/cm^3 EVA/EPE estimate (range 0.03-0.05)
reserve_ratio_target = 1.25;  // flooded: (disp/mass) >= this  (PASS >= 1.20)
sealed_reserve_min   = 3.0;   // sealed: 1000cm3/mass >= this (design ~4.83)
freeboard_min        = 30;    // mm minimum calm-water freeboard
ballast_mass_g       = 40;    // tuning var; +10 g ballast needs +~11.7 cm^3 foam
// foam collar geometry (NEW part, cut/heat-formed EVA sheet — .scad is the cut master)
foam_od     = 86;             // mm, fits inside bottle_id=90 with margin
foam_bore_l = board_l + 2;    // ~70 mm payload channel (board_l=68)
foam_bore_w = board_w + 6;    // ~40 mm (board_w=34)
foam_area   = PI*pow(foam_od/2,2)/100 - (foam_bore_l*foam_bore_w)/100; // ~30.1 cm^2
foam_collar_h = foam_vol / foam_area;   // ~53 mm; split into 2 x ~27 mm
// prints: measured STL solid volume = 56.9 cm^3 (bracket 40.4 + keel 9.95 + loop 6.57)
print_infill_max = 0.60;  // keep <=60% -> foam_vol 160 holds; solid(100%) needs ~175

// --- full assembly (real size; visual mocks measure YOUR parts) ---
collar_t   = 27;          // foam collar thickness (2 pieces = foam_collar_h ~53)
collar_x   = 44.5;        // collar center offset +-X (clears keel ends at +-29.9)
bottle_body_l = 190;      // straight body length of a ~1 L bottle (mock)
bottle_body_x0 = -100;    // body from x0 to x0+bottle_body_l; neck/cap at +X
shoulder_l = 22;          // taper body -> neck
neck_l     = 18;          // neck + cap
cap_d      = 31;          // cap outer diameter
