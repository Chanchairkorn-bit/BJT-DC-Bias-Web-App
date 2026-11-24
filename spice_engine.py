"""SPICE simulation engine adapter for BJT Common-Emitter Amplifier (Lab 04).

Invokes ngspice in batch mode using subprocess.run without shell=True,
validates all electrical parameters, parses output files, and formats
engineering results for DC (.op), AC (.ac), and Transient (.tran) analyses.
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import dc_bias


# Default BJT Model for Q2N3904
DEFAULT_BJT_MODEL = (
    "Q2N3904 NPN ("
    "Is=1E-14 Bf={beta} Vaf=100 Ikf=0.1 Xtb=1.5 Br=4 "
    "Cjc=4pF Cje=8pF Tr=30n Tf=400p)"
)


def find_ngspice() -> str:
    """Locate the ngspice executable on the system."""
    for candidate in ["ngspice_con", "ngspice"]:
        found = shutil.which(candidate)
        if found:
            return found
    # Common Windows install locations
    common_paths = [
        os.path.expanduser(r"~\Spice64\bin\ngspice_con.exe"),
        os.path.expanduser(r"~\Spice64\bin\ngspice.exe"),
        r"C:\Spice64\bin\ngspice_con.exe",
        r"C:\Spice64\bin\ngspice.exe",
        r"C:\Program Files\Spice64\bin\ngspice_con.exe",
        r"C:\Program Files\Spice64\bin\ngspice.exe",
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("ngspice executable not found in PATH or standard directories.")


@dataclass
class CircuitParams:
    vcc: float = 12.0
    r1: float = 100_000.0
    r2: float = 22_000.0
    rc: float = 2_200.0
    re: float = 1_000.0
    rl: float = 10_000.0
    cin: float = 10e-6
    cout: float = 10e-6
    beta: float = 100.0
    amplitude: float = 0.01   # Peak in V (10 mV)
    frequency: float = 1000.0 # in Hz (1 kHz)


def validate_params(params: CircuitParams) -> List[str]:
    """Validate circuit parameters before netlist generation."""
    errors = []
    if params.vcc <= 0:
        errors.append("ค่า VCC ต้องมากกว่า 0 (VCC must be positive > 0 V).")
    if params.r1 <= 0:
        errors.append("ค่า R1 ต้องมากกว่า 0 (R1 must be positive > 0 Ω).")
    if params.r2 <= 0:
        errors.append("ค่า R2 ต้องมากกว่า 0 (R2 must be positive > 0 Ω).")
    if params.rc <= 0:
        errors.append("ค่า RC ต้องมากกว่า 0 (RC must be positive > 0 Ω).")
    if params.re <= 0:
        errors.append("ค่า RE ต้องมากกว่า 0 (RE must be positive > 0 Ω).")
    if params.rl <= 0:
        errors.append("ค่า RL ต้องมากกว่า 0 (RL must be positive > 0 Ω).")
    if params.cin <= 0:
        errors.append("ค่า Cin ต้องมากกว่า 0 (Cin must be positive > 0 F).")
    if params.cout <= 0:
        errors.append("ค่า Cout ต้องมากกว่า 0 (Cout must be positive > 0 F).")
    if params.beta <= 0:
        errors.append("ค่า β (beta) ต้องมากกว่า 0 (β must be positive > 0).")
    if params.amplitude <= 0:
        errors.append("ค่า Source amplitude ต้องมากกว่า 0 (Amplitude must be positive > 0 V).")
    if params.frequency <= 0:
        errors.append("ค่า Source frequency ต้องมากกว่า 0 (Frequency must be positive > 0 Hz).")
    return errors


def generate_netlist(params: CircuitParams, mode: str, ac_file: str = "ac.txt", tran_file: str = "tran.txt") -> str:
    """Generate SPICE netlist string for the CE Voltage-Divider circuit."""
    model_line = f".model Q2N3904 NPN (Is=1e-14 Bf={params.beta} Vaf=100 Ikf=0.1 Xtb=1.5 Br=4 Cjc=4pF Cje=8pF Tr=30n Tf=400p)"
    
    # Calculate appropriate time span for transient (3 cycles)
    period = 1.0 / params.frequency
    t_stop = period * 3.0
    t_step = period / 100.0

    lines = [
        f"* ENG29 2121 Lab 04 BJT CE Amplifier Simulator",
        f"VCC vcc 0 DC {params.vcc}",
        f"VIN in 0 DC 0 AC {params.amplitude} SIN(0 {params.amplitude} {params.frequency})",
        f"R1 vcc b {params.r1}",
        f"R2 b 0 {params.r2}",
        f"RC vcc c {params.rc}",
        f"RE e 0 {params.re}",
        f"CIN in b {params.cin}",
        f"COUT c out {params.cout}",
        f"RL out 0 {params.rl}",
        f"Q1 c b e Q2N3904",
        model_line,
        f".control",
        f"set filetype=ascii",
    ]

    if mode == "dc":
        lines += [
            f"op",
            f"print v(b) v(e) v(c) v(c)-v(e) @q1[ic] @q1[ib]",
        ]
    elif mode == "ac":
        lines += [
            f"ac dec 20 1 100Meg",
            f"wrdata ac.txt vdb(out)-vdb(in) cph(v(out)/v(in))*180/pi",
        ]
    elif mode == "tran":
        lines += [
            f"tran {t_step:.3e} {t_stop:.3e}",
            f"wrdata tran.txt v(in) v(out)",
        ]
    elif mode == "all":
        lines += [
            f"op",
            f"print v(b) v(e) v(c) v(c)-v(e) @q1[ic] @q1[ib]",
            f"ac dec 20 1 100Meg",
            f"wrdata ac.txt vdb(out)-vdb(in) cph(v(out)/v(in))*180/pi",
            f"tran {t_step:.3e} {t_stop:.3e}",
            f"wrdata tran.txt v(in) v(out)",
        ]

    lines += [
        f".endc",
        f".end",
    ]
    return "\n".join(lines) + "\n"


def parse_op_output(log_text: str) -> Dict[str, float]:
    """Parse DC operating point from ngspice print output."""
    import re
    res = {}
    patterns = {
        "vb": r"v\(b\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        "ve": r"v\(e\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        "vc": r"v\(c\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        "vce": r"v\(c\)-v\(e\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        "ic": r"@q1\[ic\]\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        "ib": r"@q1\[ib\]\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, log_text, re.IGNORECASE)
        if m:
            res[key] = float(m.group(1))

    if "vb" in res and "ve" in res and "vbe" not in res:
        res["vbe"] = res["vb"] - res["ve"]

    return res


def parse_ac_file(file_path: str) -> Tuple[List[float], List[float], List[float], Dict[str, Any]]:
    """Parse AC frequency, gain in dB, and phase in degrees from wrdata output."""
    freqs = []
    gains = []
    phases = []
    if not os.path.exists(file_path):
        return freqs, gains, phases, {}

    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                try:
                    f_val = float(parts[0])
                    g_val = float(parts[1])
                    p_val = float(parts[3])
                    freqs.append(f_val)
                    gains.append(g_val)
                    phases.append(p_val)
                except ValueError:
                    continue

    meta = {}
    if gains:
        max_gain = max(gains)
        meta["midband_gain_db"] = round(max_gain, 2)
        meta["midband_gain_linear"] = round(10.0 ** (max_gain / 20.0), 2)
        target_db = max_gain - 3.0

        # Find 3dB cutoff frequencies
        max_idx = gains.index(max_gain)
        f_l = None
        for i in range(max_idx - 1, -1, -1):
            if gains[i] <= target_db:
                f_l = freqs[i]
                break

        f_h = None
        for i in range(max_idx + 1, len(gains)):
            if gains[i] <= target_db:
                f_h = freqs[i]
                break

        meta["f_low"] = f"{f_l:.1f} Hz" if f_l else "Not in sweep range"
        meta["f_high"] = f"{f_h / 1e6:.2f} MHz" if f_h and f_h >= 1e6 else (f"{f_h / 1e3:.1f} kHz" if f_h else "Not in sweep range")

    return freqs, gains, phases, meta


def parse_tran_file(file_path: str) -> Tuple[List[float], List[float], List[float], Dict[str, Any]]:
    """Parse transient time, vin, and vout from wrdata output."""
    times = []
    vins = []
    vouts = []
    if not os.path.exists(file_path):
        return times, vins, vouts, {}

    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                try:
                    t_val = float(parts[0])
                    vin_val = float(parts[1])
                    vout_val = float(parts[3])
                    times.append(t_val)
                    vins.append(vin_val)
                    vouts.append(vout_val)
                except ValueError:
                    continue

    meta = {}
    if vins and vouts:
        meta["vin_peak"] = max(abs(min(vins)), max(vins))
        meta["vout_peak"] = max(abs(min(vouts)), max(vouts))
        if meta["vin_peak"] > 0:
            meta["observed_gain"] = round(meta["vout_peak"] / meta["vin_peak"], 2)
        
        # Check phase inversion: when Vin reaches max positive, Vout should be negative
        max_vin_idx = vins.index(max(vins))
        meta["phase_inverted"] = vouts[max_vin_idx] < 0

    return times, vins, vouts, meta


def generate_svg_bode(freqs: List[float], gains: List[float], phases: List[float], width: int = 700, height: int = 300) -> str:
    """Generate self-contained clean responsive SVG Bode magnitude & phase plot."""
    if not freqs or not gains:
        return "<svg><text>No AC data available</text></svg>"

    # Margins
    ml, mr, mt, mb = 60, 60, 30, 45
    pw = width - ml - mr
    ph = height - mt - mb

    min_f = math.log10(max(freqs[0], 1e-3))
    max_f = math.log10(max(freqs[-1], 10.0))
    min_g = math.floor(min(min(gains), -20) / 10.0) * 10
    max_g = math.ceil(max(max(gains), 10) / 10.0) * 10
    min_p = -200.0
    max_p = 200.0

    def fx(f):
        lf = math.log10(max(f, 1e-3))
        return ml + (lf - min_f) / (max_f - min_f) * pw

    def gy(g):
        return mt + (max_g - g) / (max_g - min_g) * ph

    def py(p):
        return mt + (max_p - p) / (max_p - min_p) * ph

    # Build paths
    gain_pts = [f"{fx(f):.1f},{gy(g):.1f}" for f, g in zip(freqs, gains)]
    phase_pts = [f"{fx(f):.1f},{py(p):.1f}" for f, p in zip(freqs, phases)]

    gain_path = "M " + " L ".join(gain_pts)
    phase_path = "M " + " L ".join(phase_pts)

    # Grid lines
    grid = []
    # Decades
    for d in range(int(math.floor(min_f)), int(math.ceil(max_f)) + 1):
        x = fx(10**d)
        if ml <= x <= ml + pw:
            grid.append(f'<line x1="{x:.1f}" y1="{mt}" x2="{x:.1f}" y2="{mt+ph}" stroke="#e2e8f0" stroke-width="1"/>')
            label = f"10^{d}" if d < 0 or d > 3 else f"{10**d:g}"
            if d == 3: label = "1k"
            elif d == 6: label = "1M"
            grid.append(f'<text x="{x:.1f}" y="{mt+ph+18}" text-anchor="middle" font-size="11" fill="#64748b">{label}Hz</text>')

    # Gain ticks
    for g in range(int(min_g), int(max_g) + 1, 10):
        y = gy(g)
        if mt <= y <= mt + ph:
            grid.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml+pw}" y2="{y:.1f}" stroke="#e2e8f0" stroke-width="1"/>')
            grid.append(f'<text x="{ml-8}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="#0284c7">{g} dB</text>')

    svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="spice-chart" role="img" aria-label="Bode Plot">
  <rect width="{width}" height="{height}" fill="#f8fafc" rx="8"/>
  <rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#ffffff" stroke="#cbd5e1"/>
  {''.join(grid)}
  <!-- Gain curve -->
  <path d="{gain_path}" fill="none" stroke="#0284c7" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Phase curve -->
  <path d="{phase_path}" fill="none" stroke="#d97706" stroke-width="2" stroke-dasharray="4 2" stroke-linecap="round"/>
  <!-- Legend -->
  <rect x="{ml+10}" y="{mt+8}" width="190" height="26" fill="rgba(255,255,255,0.85)" rx="4"/>
  <line x1="{ml+20}" y1="{mt+21}" x2="{ml+45}" y2="{mt+21}" stroke="#0284c7" stroke-width="2.5"/>
  <text x="{ml+50}" y="{mt+25}" font-size="12" font-weight="600" fill="#0284c7">Magnitude (dB)</text>
  <line x1="{ml+145}" y1="{mt+21}" x2="{ml+170}" y2="{mt+21}" stroke="#d97706" stroke-width="2" stroke-dasharray="4 2"/>
  <text x="{ml+175}" y="{mt+25}" font-size="12" font-weight="600" fill="#d97706">Phase (°)</text>
</svg>"""
    return svg


def generate_svg_transient(times: List[float], vins: List[float], vouts: List[float], width: int = 700, height: int = 300) -> str:
    """Generate self-contained clean responsive SVG Transient waveform plot."""
    if not times or not vins or not vouts:
        return "<svg><text>No Transient data available</text></svg>"

    ml, mr, mt, mb = 60, 20, 30, 45
    pw = width - ml - mr
    ph = height - mt - mb

    t_min = times[0]
    t_max = times[-1]

    # Convert times to ms for display readability
    t_scale = 1e3
    t_label = "ms"

    v_all = vins + vouts
    v_min = min(v_all)
    v_max = max(v_all)
    v_span = max(v_max - v_min, 1e-3)
    v_min -= v_span * 0.1
    v_max += v_span * 0.1

    def tx(t):
        return ml + (t - t_min) / (t_max - t_min) * pw

    def vy(v):
        return mt + (v_max - v) / (v_max - v_min) * ph

    vin_pts = [f"{tx(t):.1f},{vy(v):.1f}" for t, v in zip(times, vins)]
    vout_pts = [f"{tx(t):.1f},{vy(v):.1f}" for t, v in zip(times, vouts)]

    vin_path = "M " + " L ".join(vin_pts)
    vout_path = "M " + " L ".join(vout_pts)

    grid = []
    # Horizontal grid
    v_zero_y = vy(0.0)
    grid.append(f'<line x1="{ml}" y1="{v_zero_y:.1f}" x2="{ml+pw}" y2="{v_zero_y:.1f}" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="3 3"/>')

    # Time ticks (5 ticks)
    for i in range(6):
        t_tick = t_min + i * (t_max - t_min) / 5.0
        x = tx(t_tick)
        grid.append(f'<line x1="{x:.1f}" y1="{mt}" x2="{x:.1f}" y2="{mt+ph}" stroke="#e2e8f0" stroke-width="1"/>')
        grid.append(f'<text x="{x:.1f}" y="{mt+ph+18}" text-anchor="middle" font-size="11" fill="#64748b">{(t_tick*t_scale):.2f}{t_label}</text>')

    # Voltage ticks
    v_steps = [v_min, v_min/2 if v_min<0 else v_min, 0.0, v_max/2 if v_max>0 else v_max, v_max]
    for v_val in [-0.02, -0.01, 0.0, 0.01, 0.02]:
        if v_min <= v_val <= v_max:
            y = vy(v_val)
            grid.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml+pw}" y2="{y:.1f}" stroke="#e2e8f0" stroke-width="1"/>')
            grid.append(f'<text x="{ml-8}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="#64748b">{v_val*1000:.0f} mV</text>')

    svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="spice-chart" role="img" aria-label="Transient Waveforms">
  <rect width="{width}" height="{height}" fill="#f8fafc" rx="8"/>
  <rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#ffffff" stroke="#cbd5e1"/>
  {''.join(grid)}
  <!-- Vin curve -->
  <path d="{vin_path}" fill="none" stroke="#0d9488" stroke-width="2.2" stroke-linecap="round"/>
  <!-- Vout curve -->
  <path d="{vout_path}" fill="none" stroke="#ea580c" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Legend -->
  <rect x="{ml+10}" y="{mt+8}" width="240" height="26" fill="rgba(255,255,255,0.85)" rx="4"/>
  <line x1="{ml+20}" y1="{mt+21}" x2="{ml+45}" y2="{mt+21}" stroke="#0d9488" stroke-width="2.2"/>
  <text x="{ml+50}" y="{mt+25}" font-size="12" font-weight="600" fill="#0d9488">Vin (In-phase, Teal)</text>
  <line x1="{ml+170}" y1="{mt+21}" x2="{ml+195}" y2="{mt+21}" stroke="#ea580c" stroke-width="2.5"/>
  <text x="{ml+200}" y="{mt+25}" font-size="12" font-weight="600" fill="#ea580c">Vout (180° Inverted)</text>
</svg>"""
    return svg


def run_simulation(params: CircuitParams, mode: str = "dc") -> Dict[str, Any]:
    """Execute ngspice simulation for the given circuit parameters and mode.
    
    mode can be: 'dc', 'ac', 'tran', or 'all'
    Returns a dict containing parsed values, charts, log, status, and analytical comparison.
    """
    validation_errors = validate_params(params)
    if validation_errors:
        return {
            "status": "error",
            "errors": validation_errors,
            "mode": mode,
        }

    try:
        ngspice_cmd = find_ngspice()
    except FileNotFoundError as e:
        return {
            "status": "error",
            "errors": [f"Simulation engine not available: {e}"],
            "mode": mode,
        }

    # Run in an isolated temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        netlist_file = os.path.join(tmpdir, "circuit.cir")
        ac_file = os.path.join(tmpdir, "ac.txt")
        tran_file = os.path.join(tmpdir, "tran.txt")

        netlist_str = generate_netlist(params, mode, ac_file=ac_file, tran_file=tran_file)
        with open(netlist_file, "w", encoding="ascii") as f:
            f.write(netlist_str)

        try:
            cmd = [ngspice_cmd, "-b", "circuit.cir"]
            proc = subprocess.run(
                cmd,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "errors": ["Simulation timed out after 15 seconds."],
                "mode": mode,
            }
        except Exception as ex:
            return {
                "status": "error",
                "errors": [f"Subprocess execution failed: {ex}"],
                "mode": mode,
            }

        combined_log = (proc.stdout or "") + "\n" + (proc.stderr or "")

        result: Dict[str, Any] = {
            "status": "success",
            "mode": mode,
            "engine": "ngspice-47",
            "bjt_model": f"Q2N3904 (β={params.beta})",
            "log": combined_log,
        }

        # DC operating point (always parse if present or requested)
        if mode in ("dc", "all"):
            dc_res = parse_op_output(combined_log)
            if not dc_res:
                result["status"] = "error"
                result["errors"] = ["Failed to extract DC operating point from ngspice output."]
                return result
            result["dc"] = dc_res

            # Analytical comparison from Lab 3 dc_bias
            analytical = dc_bias.calculate(
                vcc=params.vcc,
                r1=params.r1,
                r2=params.r2,
                rc=params.rc,
                re=params.re,
                beta=params.beta,
                vbe=0.70,
            )
            result["analytical"] = {
                "vb": analytical.vb,
                "ve": analytical.ve,
                "vc": analytical.vc,
                "vce": analytical.vce,
                "ic": analytical.ic,
                "ib": analytical.ib,
                "region": analytical.region,
            }

        # AC response
        if mode in ("ac", "all"):
            freqs, gains, phases, ac_meta = parse_ac_file(ac_file)
            if not freqs or not gains:
                result["status"] = "error"
                result["errors"] = ["AC analysis produced no output data."]
                return result
            result["ac"] = {
                "meta": ac_meta,
                "svg": generate_svg_bode(freqs, gains, phases),
                "data_points": len(freqs),
            }

        # Transient response
        if mode in ("tran", "all"):
            times, vins, vouts, tran_meta = parse_tran_file(tran_file)
            if not times or not vins:
                result["status"] = "error"
                result["errors"] = ["Transient analysis produced no output data."]
                return result
            result["tran"] = {
                "meta": tran_meta,
                "svg": generate_svg_transient(times, vins, vouts),
                "data_points": len(times),
            }

        return result
