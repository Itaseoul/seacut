// SEA:CUT / Friendly Floatee drifter — shared parameters (mm)
// Hardware: CERN-OHL-S v2 (strongly reciprocal). Docs: CC BY-SA 4.0. Firmware: MIT.
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
ballast_mass_g       = 40;    // tuning var; +10 g ballast needs +~11.8 cm^3 foam (1-R*rho_foam; solar=6.7)
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

// ============================================================
//  Tier 1.5 SOLAR VARIANT — parameters (NEW; every value an ESTIMATE -> bench-verify)
//  Anchors: buoyancy=RELIABILITY §4 (density-aware) · RF=FLOAT_STANDARD B5
//           self-right "T7" = VERIFIED_BUILD_TEST T4 re-run with the solar payload installed
//  Kernels enforced here: NO new printed part · ballast 40 g UNCHANGED ·
//                         non-metal cells only · solar = power != coverage
// ------------------------------------------------------------
solar_enable = 0;          // 0 = plain Tier 1 (default). Solar build: set 1 or render -D solar_enable=1.
                           // ★SHORT-RECOVERY MISSIONS keep 0 (ELECTRONICS_POWER §3: solar = net loss).

bl_ref = board_l + 2*wall + 2*clr;                 // 73.6 (bracket len; ribs at +-bl_ref*0.35 = +-25.76)

// --- added-mass budget (★MEASURE; lens estimates diverge 20-45 g) ---
solar_added_mass_g = 39;   // PLANNING nominal (film 10-25 + ctrl 5-8 + wire 3-4 + vent ~2 + adhesive 3-8)
solar_add_rho      = 1.64; // g/cm^3 EFFECTIVE (film~1.65 · PCB~1.9 · wire~1.5 · adhesive~1.0)
solar_second_cell  = 0;    // 1 => +~56 g (48 cell + 8 mount), BELLY only, matched cells + isolation diode (F2/T7 re-pass)
solar_added_mass_eff = solar_added_mass_g + (solar_second_cell ? 56 : 0);  // effective Δm fed to foam sizing

// --- density-aware foam re-size (★NOT the ballast 11.7 cm^3/10g; panel is low-density) ---
solar_foam_coeff = (1.25 - 1/solar_add_rho)/(1 - 1.25*foam_density)*10;  // ~6.7 cm^3 / 10 g
foam_vol_solar   = foam_vol + solar_foam_coeff*(solar_added_mass_eff/10);  // ~186 cm^3 @ 39 g (2nd cell => ~224)
collar_t_solar   = foam_vol_solar/foam_area*10/2;                        // ~31 mm each (2 collars); assembly/export use this

// --- wrap bands (★NOT printed: laminated film + marine adhesive on the body) ---
solar_wrap_od = bottle_id + 2;   // body OD (MEASURE yours)
solar_wrap_r  = solar_wrap_od/2;
solar_film_t  = 0.8;             // laminated film thickness (fit/collision + RF-window viz ONLY)
solar_band_n  = 2;
solar_band_w  = 44;              // axial band width
solar_band_gap= 34;              // central channel >= recovery-loop base 30 (loop + QR stay bare)
solar_band_x  = [ for (i=[0:solar_band_n-1])
                  (solar_band_n==1) ? 0 : (i-(solar_band_n-1)/2)*(solar_band_w+solar_band_gap) ]; // +-39

// --- RF keep-out (★REAL gate = non-metal substrate; the film window is secondary insurance) ---
solar_cell_substrate = "nonmetal"; // HARD GATE: a-Si / polyimide ONLY. "metal" => ABORT (B5; verify T6)
solar_rf_x0 = -50; solar_rf_x1 = 48;  // antenna x-range (doc only; the window currently cuts the full band length)
solar_rf_deg = 120;                   // top +Z sector kept FILM-FREE (cut across the whole band = conservative)

// --- charge path (★default EXTERNAL low-Iq linear -> BATTERY terminal; NOT onboard-direct) ---
solar_ctrl_mode = "linear";  // "linear"=CN3065-class low-Iq (DEFAULT) | "mppt"=CN3791-class (clean sites)
solar_ctrl_l=26; solar_ctrl_w=19; solar_ctrl_h=7;   // COTS envelope (CG viz only), zip-tied to bracket rib
solar_ctrl_x = -bl_ref*0.35;  // -25.76 : on the -X bracket locating rib
solar_ctrl_z = -2;            // just below centreline, BESIDE the cell holder (keep CG low -> T7)

// --- low-temp cutoff (★MANDATORY on ALL modes — HARDWARE latch, not firmware) ---
solar_ntc = "10k_B3435_cell_bonded";  // JEITA: <0C stop · 0-10C taper · >45C stop (epoxy to cell can)

// --- wiring: REUSE the resealed-seam grommet (assembly §3-0) — NO NEW HOLE; re-pass T1 ---
solar_wire_od = 3.0;
// --- vent: Gore-Tex ePTFE ADHESIVE PATCH on the cap (NOT a printed boss) ---
solar_vent_patch_d = 19;

// ★HARD GATE (FLOAT_STANDARD B5) — makes the "metal => ABORT" claim TRUE in code, not just prose.
//   Any file that includes params.scad aborts if a metal-backed cell substrate is selected.
assert(solar_cell_substrate != "metal",
       "B5: metal-backed solar cells shield the antennas (RF death) + are toxic -> ABORT. Use a-Si (ETFE) or Cd-free CIGS (polyimide).");
