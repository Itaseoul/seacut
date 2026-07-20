#!/usr/bin/env python3
"""Self-righting design check (metacentric height) for the belly-ballasted bottle.

Turns "self-rights antenna-up" from an assertion into a computed number. The float lies
HORIZONTAL (schema calibration form.attitude), so this is roll stability of a partly
submerged circular cylinder. It computes GM = KB + BM - KG and a large-angle righting-arm
proxy, and prints PASS/FAIL.

★HONEST LIMITS (do not oversell this):
  * Small-angle metacentric theory. GM governs the *initial* righting slope; the full GZ curve
    (and the guarantee of a SINGLE stable equilibrium = antenna-up) needs the submerged geometry
    recomputed at every heel angle. That, and the real answer, come from the tank test
    (VERIFIED_BUILD_TEST T4 / solar T7) — this script does not replace it.
  * Uniform prismatic section (ignores neck/cap taper, ends). Masses are ESTIMATES; edit them.
  * Assumes intact (sealed) float. A flooded hull is the buoyancy problem in RELIABILITY, not this.

Defaults mirror hardware/cad/params.scad. Pure stdlib. CC BY-SA 4.0 (docs) / MIT (code).
Usage:  python3 hardware/cad/self_righting.py [--mass G] [--ballast-z MM] [--solar] [--json]
  --solar models the Tier 1.5 solar kit on top of the base build (still an ESTIMATE; the
  tank test T7 = self-right WITH cells is the only real judge, per TIER1_5_SOLAR_DRIFTER.md).
"""
import argparse
import json
import math

RHO_W = 1.000e-3   # g/mm^3  fresh water (schema medium=freshwater)

# --- geometry (mm), from params.scad ---
BOTTLE_ID = 90.0
R = BOTTLE_ID / 2.0          # 45 mm inner radius
BODY_L = 190.0              # straight body length (the prismatic part that floats)

# --- mass budget (g, z = height above the KEEL = lowest point of the circle, mm) ---
# z runs 0..2R (0 = belly/keel, R = section center, 2R = top where the antenna exits).
# EDIT THESE per your build; they are estimates. Ballast low, antenna high is the whole design.
def default_components():
    return [
        # name,            mass_g, z_mm (centroid height above keel)
        ("lead-free ballast", 40.0,  7.0),   # in the belly pocket, as low as it packs
        ("18650 cell",        47.0, 38.0),   # in the bracket, just below section center
        ("A7670G board",      20.0, 52.0),   # above center (antenna end up)
        ("foam collar",        6.4, 45.0),   # ~160 cm^3 * 0.04 g/cm^3, distributed near center
        ("PET housing",       30.0, 45.0),   # thin shell, centroid ~ section center
        ("misc (wire/seal)",  10.0, 45.0),
        ("printed inserts",   35.0, 35.0),   # bracket+keel+loop (keel low, loop high -> blended ~35)
        ("antennas",           8.0, 58.0),   # LTE+GNSS, exit high near the top
    ]
    # NOTE: this sums to ~196 g, matching the canonical M_dry~199 / M_wet~207 budget
    # (RELIABILITY/params). An earlier 153 g version omitted inserts+antennas and over-stated GM
    # (~11 mm); with the full mass GM lands ~10 mm — still PASS, but do not quote the old number.


def solar_components():
    """Tier 1.5 add-on (TIER1_5_SOLAR_DRIFTER). The wrapped film's centroid sits on the section
    AXIS (z=R) by symmetry, so it barely moves CG; the controller on the bracket is slightly high.
    Masses are estimates — T7 (self-right WITH cells) is the judge."""
    return [
        ("solar film (wrapped)",      15.0, 45.0),
        ("charge ctrl+NTC+diode",     12.0, 52.0),
        ("extra foam (solar re-cut)",  3.0, 45.0),
    ]


def seg_area(h):
    """Submerged circular-segment area (mm^2) for waterline at height h above keel, radius R."""
    h = max(0.0, min(2 * R, h))
    if h <= 0:
        return 0.0
    if h >= 2 * R:
        return math.pi * R * R
    return R * R * math.acos((R - h) / R) - (R - h) * math.sqrt(2 * R * h - h * h)


def solve_waterline(disp_area_target):
    """Bisect for waterline height h so seg_area(h) == target (mm^2)."""
    lo, hi = 0.0, 2 * R
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if seg_area(mid) < disp_area_target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def kb_of(h, n=4000):
    """Centroid height (mm above keel) of the submerged area, by numeric integration."""
    if h <= 0:
        return 0.0
    dz = h / n
    num = den = 0.0
    for i in range(n):
        z = (i + 0.5) * dz
        w = 2.0 * math.sqrt(max(0.0, R * R - (z - R) ** 2))   # chord width at height z
        num += z * w * dz
        den += w * dz
    return num / den if den else 0.0


def check(mass_g, components, verbose=True, as_json=False):
    V = mass_g / RHO_W                     # displaced volume needed (mm^3)
    disp_area = V / BODY_L                 # submerged cross-section area (mm^2)
    full_area = math.pi * R * R
    if disp_area >= full_area:
        raise SystemExit("mass exceeds prismatic buoyancy — it would sink or ride on ends; re-check mass/geometry")
    h = solve_waterline(disp_area)         # waterline height above keel
    submerged_frac = disp_area / full_area
    freeboard = 2 * R - h                  # top of circle minus waterline

    KB = kb_of(h)
    b = 2.0 * math.sqrt(max(0.0, 2 * R * h - h * h))   # waterplane beam (chord at waterline)
    I_wl = BODY_L * b ** 3 / 12.0
    BM = I_wl / V
    KG = sum(m * z for _, m, z in components) / sum(m for _, m, z in components)
    KM = KB + BM                            # keel-to-metacenter
    GM = KM - KG
    BG = KB - KG                            # reported only; G-above-B (BG<0) is NORMAL for a surface float

    # ★Circular-section property: for a prismatic circular hull the metacenter sits on the section
    #   AXIS (KM = R) at any draft — so GM = R - KG, and the large-angle righting arm is the same
    #   pendulum GZ(phi) = GM * sin(phi). This makes the design rule exact and memorable:
    #   keep the combined CG below the bottle's central axis. (Sanity: KM should print ~= R.)
    gz = {deg: GM * math.sin(math.radians(deg)) for deg in (10, 30, 45, 60, 90)}

    # Correct criterion for a SURFACE float is GM>0 (not G-below-B). We want margin, and we want the
    # single stable equilibrium to be antenna-up, i.e. G below the section axis: KG < R.
    PASS = GM > 5.0 and KG < R - 3.0

    res = {
        "mass_g": round(mass_g, 1),
        "submerged_fraction": round(submerged_frac, 3),
        "waterline_h_mm": round(h, 1),
        "freeboard_mm": round(freeboard, 1),
        "KB_mm": round(KB, 1), "KG_mm": round(KG, 1), "BM_mm": round(BM, 1),
        "KM_mm": round(KM, 1), "section_axis_R_mm": round(R, 1),
        "GM_mm": round(GM, 1), "BG_mm": round(BG, 1),
        "GZ_pendulum_mm": {k: round(v, 1) for k, v in gz.items()},
        "verdict": "PASS" if PASS else "FAIL",
    }
    if as_json:
        print(json.dumps(res, indent=2))
        return res
    if verbose:
        print(f"  mass {mass_g:.0f} g  ->  submerged {submerged_frac*100:.0f}%  "
              f"waterline {h:.1f} mm  freeboard {freeboard:.1f} mm")
        print(f"  KB {KB:.1f}  BM {BM:.1f}  ->  KM {KM:.1f} mm (~= axis R={R:.0f}, circular-section property)")
        print(f"  KG {KG:.1f} mm  (must be < axis {R:.0f} for antenna-up)   ->  GM = R - KG = {GM:.1f} mm")
        print("  righting arm GZ(phi) = GM*sin(phi):  " +
              "  ".join(f"{d}deg={v:.1f}" for d, v in gz.items()) + " mm")
        print(f"  VERDICT: {res['verdict']}  (need GM>5 mm and KG<{R-3:.0f} mm; "
              f"antenna-up single-equilibrium confirmed only by tank test T4/T7)")
    return res


def main():
    ap = argparse.ArgumentParser(description="Belly-ballasted bottle self-righting (GM) check")
    ap.add_argument("--mass", type=float, default=None, help="total mass g (default: sum of components)")
    ap.add_argument("--ballast-z", type=float, default=None, help="override ballast centroid height mm")
    ap.add_argument("--solar", action="store_true", help="model the Tier 1.5 solar kit (film+controller+foam)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    comp = default_components()
    if a.solar:
        comp = comp + solar_components()   # Tier 1.5 build: pre-check GM with the solar kit on
    if a.ballast_z is not None:
        comp[0] = (comp[0][0], comp[0][1], a.ballast_z)
    mass = a.mass if a.mass is not None else sum(m for _, m, _ in comp)
    res = check(mass, comp, verbose=not a.json, as_json=a.json)
    raise SystemExit(0 if res["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
