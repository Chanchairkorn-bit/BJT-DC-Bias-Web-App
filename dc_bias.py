"""DC bias calculations for BJT amplifier bias topologies.

Supported topologies
--------------------
1. ``voltage-divider`` : R1/R2 divider at the base, RC collector, RE emitter.
2. ``fixed``           : RB from VCC to the base, RC collector, emitter grounded.
3. ``emitter``         : RB from VCC to the base, RC collector, RE emitter.

This module contains pure engineering logic. It must NOT import Flask,
HTML or any web framework. All values are expressed in SI units:
volts (V), ohms (Ohm) and amperes (A).

The forward-active approximation uses a constant beta and constant VBE.
Outside the forward-active region the result is flagged with a warning
instead of being reported as trustworthy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# Typical collector-emitter saturation voltage, used only to decide when
# to warn that the forward-active assumption no longer holds.
VCE_SAT = 0.2  # V


@dataclass
class BiasResult:
    """Result of a single DC bias calculation (SI units)."""

    bias_type: str
    vcc: float
    rc: float
    beta: float
    vbe: float

    ib: float   # base current [A]
    ic: float   # collector current [A]
    ie: float   # emitter current [A]

    vb: float   # base voltage [V]
    ve: float   # emitter voltage [V]
    vc: float   # collector voltage [V]
    vce: float  # collector-emitter voltage [V]

    # Voltage-divider only
    r1: Optional[float] = None
    r2: Optional[float] = None
    vth: Optional[float] = None
    rth: Optional[float] = None

    # Bias / emitter resistor (fixed and emitter bias)
    rb: Optional[float] = None
    re: Optional[float] = None

    region: str = "unknown"
    warnings: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Validation helpers
# --------------------------------------------------------------------------
def _validate_common(vcc, rc, beta, vbe):
    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0 V")
    if rc <= 0:
        raise ValueError("RC ต้องมากกว่า 0 Ω")
    if beta <= 0:
        raise ValueError("β (beta) ต้องมากกว่า 0")
    if vbe < 0:
        raise ValueError("VBE ต้องไม่ติดลบ")
    if vbe >= vcc:
        raise ValueError("VBE ต้องน้อยกว่า VCC")


def _validate_resistor(name, value):
    if value <= 0:
        raise ValueError(f"{name} ต้องมากกว่า 0 Ω")


def _sat_warning(vce):
    return (
        f"VCE = {vce:.3f} V ต่ำกว่า VCE(sat) ≈ {VCE_SAT:.1f} V: "
        "ทรานซิสเตอร์อาจอยู่ในโหมด Saturation ผลจากสมการ Forward-Active ใช้ไม่ได้"
    )


# --------------------------------------------------------------------------
# 1. Voltage-divider bias
# --------------------------------------------------------------------------
def calculate(vcc, r1, r2, rc, re, beta, vbe) -> BiasResult:
    """Voltage-divider bias.

    VTH = VCC*R2/(R1+R2)
    RTH = R1*R2/(R1+R2)
    IB  = (VTH-VBE)/(RTH+(beta+1)*RE)
    """
    _validate_common(vcc, rc, beta, vbe)
    _validate_resistor("R1", r1)
    _validate_resistor("R2", r2)
    _validate_resistor("RE", re)

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    if vth <= vbe:
        return BiasResult(
            bias_type="voltage-divider",
            vcc=vcc, rc=rc, beta=beta, vbe=vbe,
            r1=r1, r2=r2, rb=None, re=re, vth=vth, rth=rth,
            ib=0.0, ic=0.0, ie=0.0,
            vb=vth, ve=0.0, vc=vcc, vce=vcc,
            region="cutoff",
            warnings=[
                f"VTH = {vth:.3f} V ไม่มากกว่า VBE = {vbe:.3f} V: "
                "ทรานซิสเตอร์อยู่ในโหมด Cutoff ผลจากสมการ Forward-Active ใช้ไม่ได้"
            ],
        )

    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    if vce < VCE_SAT:
        region, warnings = "saturation", [_sat_warning(vce)]
    else:
        region, warnings = "forward-active", []

    return BiasResult(
        bias_type="voltage-divider",
        vcc=vcc, rc=rc, beta=beta, vbe=vbe,
        r1=r1, r2=r2, rb=None, re=re, vth=vth, rth=rth,
        ib=ib, ic=ic, ie=ie,
        vb=vb, ve=ve, vc=vc, vce=vce,
        region=region, warnings=warnings,
    )


# --------------------------------------------------------------------------
# 2. Fixed bias (base resistor from VCC, emitter grounded)
# --------------------------------------------------------------------------
def calculate_fixed(vcc, rb, rc, beta, vbe) -> BiasResult:
    """Fixed bias.

    IB = (VCC - VBE)/RB, emitter grounded (VE = 0), VCE = VC.
    """
    _validate_common(vcc, rc, beta, vbe)
    _validate_resistor("RB", rb)

    if vcc <= vbe:
        return BiasResult(
            bias_type="fixed",
            vcc=vcc, rc=rc, beta=beta, vbe=vbe,
            rb=rb, re=None,
            ib=0.0, ic=0.0, ie=0.0,
            vb=vcc, ve=0.0, vc=vcc, vce=vcc,
            region="cutoff",
            warnings=[
                "VCC ไม่มากกว่า VBE: ทรานซิสเตอร์อยู่ในโหมด Cutoff "
                "ผลจากสมการ Forward-Active ใช้ไม่ได้"
            ],
        )

    ib = (vcc - vbe) / rb
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = 0.0
    vb = vbe
    vc = vcc - ic * rc
    vce = vc  # VE = 0

    if vce < VCE_SAT:
        region, warnings = "saturation", [_sat_warning(vce)]
    else:
        region, warnings = "forward-active", []

    return BiasResult(
        bias_type="fixed",
        vcc=vcc, rc=rc, beta=beta, vbe=vbe,
        rb=rb, re=None,
        ib=ib, ic=ic, ie=ie,
        vb=vb, ve=ve, vc=vc, vce=vce,
        region=region, warnings=warnings,
    )


# --------------------------------------------------------------------------
# 3. Emitter bias (base resistor from VCC + emitter resistor)
# --------------------------------------------------------------------------
def calculate_emitter(vcc, rb, rc, re, beta, vbe) -> BiasResult:
    """Emitter (emitter-stabilized) bias.

    IB = (VCC - VBE)/(RB + (beta+1)*RE)
    """
    _validate_common(vcc, rc, beta, vbe)
    _validate_resistor("RB", rb)
    _validate_resistor("RE", re)

    if vcc <= vbe:
        return BiasResult(
            bias_type="emitter",
            vcc=vcc, rc=rc, beta=beta, vbe=vbe,
            rb=rb, re=re,
            ib=0.0, ic=0.0, ie=0.0,
            vb=vcc, ve=0.0, vc=vcc, vce=vcc,
            region="cutoff",
            warnings=[
                "VCC ไม่มากกว่า VBE: ทรานซิสเตอร์อยู่ในโหมด Cutoff "
                "ผลจากสมการ Forward-Active ใช้ไม่ได้"
            ],
        )

    ib = (vcc - vbe) / (rb + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    if vce < VCE_SAT:
        region, warnings = "saturation", [_sat_warning(vce)]
    else:
        region, warnings = "forward-active", []

    return BiasResult(
        bias_type="emitter",
        vcc=vcc, rc=rc, beta=beta, vbe=vbe,
        rb=rb, re=re,
        ib=ib, ic=ic, ie=ie,
        vb=vb, ve=ve, vc=vc, vce=vce,
        region=region, warnings=warnings,
    )


def calculate_by_type(bias_type: str, **params) -> BiasResult:
    """Dispatch to the calculation for the requested bias topology."""
    if bias_type == "voltage-divider":
        return calculate(**params)
    if bias_type == "fixed":
        return calculate_fixed(**params)
    if bias_type == "emitter":
        return calculate_emitter(**params)
    raise ValueError(f"ไม่รู้จักชนิดไบอัส: {bias_type}")
