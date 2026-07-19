#!/usr/bin/env python3
"""Export FF-ID observation records to international standards.

Reads FF-ID observation records (one JSON object per line, the §2 form in schema.md)
and writes:
  * OGC SensorThings API Observations  (--sta out.sta.json)  — pure stdlib, always works
  * CF-1.11 trajectory CDL             (--cdl out.cdl)       — feed to `ncgen -o out.nc out.cdl`

If the optional `netCDF4` package is importable, --nc out.nc writes a real CF-NetCDF file
directly. It is never required.

This is standards-SHAPED output, not a certification. Validate with a CF-checker / an STA
endpoint / EMODnet ingestion before any real submission. See docs/DATA_STANDARDS_CROSSWALK.md.
The honesty flags (qc.*, provenance.*, is_estimate, position_uncertainty_m) are carried
through on purpose — never drop them on export. CC BY 4.0.
"""
import argparse
import datetime as _dt
import json
import sys


def _epoch_seconds(iso):
    """ISO-8601 UTC (…Z or +00:00) -> float seconds since 1970-01-01T00:00:00Z."""
    if not iso:
        return None
    s = iso.strip().replace("Z", "+00:00")
    try:
        d = _dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=_dt.timezone.utc)
    return d.timestamp()


def load(path):
    """Yield FF-ID observation dicts from a JSON-lines file (skip blanks/bad lines)."""
    fh = sys.stdin if path == "-" else open(path, encoding="utf-8")
    with fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"skip line {n}: {e}", file=sys.stderr)


def _traj_id(rec):
    return rec.get("unit_id") or rec.get("device_id") or "unknown"


def to_sensorthings(records):
    """FF-ID records -> a list of OGC SensorThings Observations (dicts)."""
    out = []
    for r in records:
        lon, lat = r.get("lon"), r.get("lat")
        obs = {
            "@iot.id": r.get("obs_id"),
            "phenomenonTime": r.get("ts_fix"),
            "resultTime": r.get("server_recv_ts"),
            # a position "result" is carried both as the value and as the FeatureOfInterest geometry
            "result": [lon, lat],
            "FeatureOfInterest": {
                "encodingType": "application/geo+json",
                "feature": {"type": "Point", "coordinates": [lon, lat]},
            },
            "Datastream": {"name": f"{_traj_id(r)}:position"},
            "parameters": {
                k: v for k, v in {
                    "trajectory_id": _traj_id(r),
                    "crs": r.get("crs", "EPSG:4326"),
                    "position_uncertainty_m": r.get("position_uncertainty_m"),
                    "fix_quality": r.get("fix_quality"),
                    "gnss_source": r.get("gnss_source"),
                    "motion_state": r.get("motion_state"),
                    "sample_interval_s": r.get("sample_interval_s"),
                    "batt_V": r.get("batt"),
                    "env": r.get("env"),
                    "qc": r.get("qc"),
                    "provenance": r.get("provenance"),
                    "medium": r.get("medium"),
                    "link": r.get("link"),
                    "license": r.get("license", "CC BY 4.0"),
                }.items() if v is not None
            },
        }
        out.append(obs)
    return out


def _cdl_escape(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def to_cdl(records):
    """FF-ID records -> a CF-1.11 trajectory CDL string (indexed ragged array)."""
    recs = list(records)
    trajs = []
    idx = {}
    rows = []  # (traj_index, time_s, lat, lon, unc)
    for r in recs:
        tid = _traj_id(r)
        if tid not in idx:
            idx[tid] = len(trajs)
            trajs.append(tid)
        rows.append((
            idx[tid],
            _epoch_seconds(r.get("ts_fix") or r.get("server_recv_ts")),
            r.get("lat"), r.get("lon"),
            r.get("position_uncertainty_m"),
        ))
    n_obs = len(rows)
    n_traj = len(trajs)
    strlen = max((len(t) for t in trajs), default=1)

    def col(i, fmt):
        vals = []
        for row in rows:
            v = row[i]
            vals.append("_" if v is None else (fmt % v))
        return ", ".join(vals) if vals else "_"

    L = []
    L.append("netcdf ff_trajectory {")
    L.append("dimensions:")
    L.append(f"    obs = {n_obs if n_obs else 1} ;")
    L.append(f"    trajectory = {n_traj if n_traj else 1} ;")
    L.append(f"    name_strlen = {strlen} ;")
    L.append("variables:")
    L.append("    char trajectory(trajectory, name_strlen) ;")
    L.append('        trajectory:cf_role = "trajectory_id" ;')
    L.append("    int trajectory_index(obs) ;")
    L.append('        trajectory_index:long_name = "index of the trajectory this obs belongs to" ;')
    L.append('        trajectory_index:instance_dimension = "trajectory" ;')
    L.append("    double time(obs) ;")
    L.append('        time:standard_name = "time" ;')
    L.append('        time:units = "seconds since 1970-01-01T00:00:00Z" ;')
    L.append("    double lat(obs) ;")
    L.append('        lat:standard_name = "latitude" ;')
    L.append('        lat:units = "degrees_north" ;')
    L.append("    double lon(obs) ;")
    L.append('        lon:standard_name = "longitude" ;')
    L.append('        lon:units = "degrees_east" ;')
    L.append("    float position_uncertainty(obs) ;")
    L.append('        position_uncertainty:long_name = "position uncertainty (GNSS CEP / HDOP*UERE)" ;')
    L.append('        position_uncertainty:units = "m" ;')
    L.append('    :featureType = "trajectory" ;')
    L.append('    :Conventions = "CF-1.11" ;')
    L.append('    :title = "Friendly Floaty (SEA:CUT) drifter trajectories" ;')
    L.append('    :summary = "Citizen-science river-to-sea litter drifter tracks. Effort/path signal, not pollution flux. Fair-weather, near-coast, surface; right-censored at the cellular edge." ;')
    L.append('    :license = "CC BY 4.0" ;')
    L.append("data:")
    L.append(" trajectory = " + (", ".join(f'"{_cdl_escape(t)}"' for t in trajs) or '""') + " ;")
    L.append(" trajectory_index = " + (", ".join(str(r[0]) for r in rows) or "0") + " ;")
    L.append(" time = " + col(1, "%.3f") + " ;")
    L.append(" lat = " + col(2, "%.6f") + " ;")
    L.append(" lon = " + col(3, "%.6f") + " ;")
    L.append(" position_uncertainty = " + col(4, "%.2f") + " ;")
    L.append("}")
    return "\n".join(L) + "\n"


def try_write_netcdf(records, path):
    """Write a real CF-NetCDF only if netCDF4 is importable; else advise ncgen."""
    try:
        import netCDF4  # noqa: F401
    except Exception:
        print("netCDF4 not installed — skipping --nc. Use --cdl then: ncgen -o out.nc out.cdl",
              file=sys.stderr)
        return False
    import netCDF4
    recs = list(records)
    trajs, idx, rows = [], {}, []
    for r in recs:
        tid = _traj_id(r)
        if tid not in idx:
            idx[tid] = len(trajs); trajs.append(tid)
        rows.append((idx[tid], _epoch_seconds(r.get("ts_fix") or r.get("server_recv_ts")),
                     r.get("lat"), r.get("lon"), r.get("position_uncertainty_m")))
    ds = netCDF4.Dataset(path, "w", format="NETCDF4")
    ds.featureType = "trajectory"; ds.Conventions = "CF-1.11"; ds.license = "CC BY 4.0"
    ds.title = "Friendly Floaty (SEA:CUT) drifter trajectories"
    ds.createDimension("obs", len(rows)); ds.createDimension("trajectory", len(trajs))
    tv = ds.createVariable("trajectory", str, ("trajectory",)); tv.cf_role = "trajectory_id"
    for i, t in enumerate(trajs):
        tv[i] = t
    ti = ds.createVariable("trajectory_index", "i4", ("obs",)); ti.instance_dimension = "trajectory"
    tm = ds.createVariable("time", "f8", ("obs",)); tm.standard_name = "time"
    tm.units = "seconds since 1970-01-01T00:00:00Z"
    la = ds.createVariable("lat", "f8", ("obs",)); la.standard_name = "latitude"; la.units = "degrees_north"
    lo = ds.createVariable("lon", "f8", ("obs",)); lo.standard_name = "longitude"; lo.units = "degrees_east"
    pu = ds.createVariable("position_uncertainty", "f4", ("obs",)); pu.units = "m"
    for j, row in enumerate(rows):
        ti[j] = row[0]
        if row[1] is not None: tm[j] = row[1]
        if row[2] is not None: la[j] = row[2]
        if row[3] is not None: lo[j] = row[3]
        if row[4] is not None: pu[j] = row[4]
    ds.close()
    print(f"wrote {path}", file=sys.stderr)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="Export FF-ID records to STA / CF-NetCDF.")
    ap.add_argument("input", help="FF-ID observation records, JSON lines ('-' for stdin)")
    ap.add_argument("--sta", help="write OGC SensorThings Observations JSON here")
    ap.add_argument("--cdl", help="write CF-1.11 trajectory CDL here (ncgen-ready)")
    ap.add_argument("--nc", help="write CF-NetCDF here (requires netCDF4)")
    args = ap.parse_args(argv)
    if not (args.sta or args.cdl or args.nc):
        ap.error("choose at least one of --sta / --cdl / --nc")

    records = list(load(args.input))
    if args.sta:
        with open(args.sta, "w", encoding="utf-8") as f:
            json.dump({"value": to_sensorthings(records)}, f, ensure_ascii=False, indent=2)
        print(f"wrote {args.sta} ({len(records)} observations)", file=sys.stderr)
    if args.cdl:
        with open(args.cdl, "w", encoding="utf-8") as f:
            f.write(to_cdl(records))
        print(f"wrote {args.cdl}", file=sys.stderr)
    if args.nc:
        try_write_netcdf(records, args.nc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
