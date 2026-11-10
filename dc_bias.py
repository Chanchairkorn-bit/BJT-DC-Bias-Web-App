"""DC bias calculations for a BJT common-emitter amplifier using
voltage-divider bias.

This module contains pure engineering logic. It must NOT import Flask,
HTML or any web framework. All values are expressed in SI units:
volts (V), ohms (Ohm) and amperes (A).

Model
-----
Forward-active approximation with a constant beta and a constant VBE:

    VTH = VCC * R2 / (R1 + R2)
    RTH = R1 * R2 / (R1 + R2)
    IB  = (VTH - VBE) / (RTH + (beta + 1) * RE)
    IC  = beta * IB
    IE  = (beta + 1) * IB
    VE  = IE * RE
    VB  = VE + VBE
    VC  = VCC - IC * RC
    VCE = VC - VE

The model is only valid in the forward-active region. When the inputs
push the device into cutoff or saturation the result is flagged with a
warning instead of being reported as trustworthy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

# Typical collector-emitter saturation voltage, used only to decide when
# to warn that the forward-active assumption no longer holds.
VCE_SAT = 0.2  # V


@dataclass
class BiasResult:
    """Result of a single DC bias calculation (SI units)."""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float

    vth: float  # Thevenin base voltage [V]
    rth: float  # Thevenin base resistance [Ohm]
    ib: float   # base current [A]
    ic: float   # collector current [A]
    ie: float   # emitter current [A]

    vb: float   # base voltage [V]
    ve: float   # emitter voltage [V]
    vc: float   # collector voltage [V]
    vce: float  # collector-emitter voltage [V]

    region: str = "unknown"
    warnings: List[str] = field(default_factory=list)


def _validate(vcc, r1, r2, rc, re, beta, vbe):
    """Validate inputs and raise ValueError with a readable message."""
    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0 V")
    for name, value in (("R1", r1), ("R2", r2), ("RC", rc), ("RE", re)):
        if value <= 0:
            raise ValueError(f"{name} ต้องมากกว่า 0 Ω")
    if beta <= 0:
        raise ValueError("β (beta) ต้องมากกว่า 0")
    if vbe < 0:
        raise ValueError("VBE ต้องไม่ติดลบ")
    if vbe >= vcc:
        raise ValueError("VBE ต้องน้อยกว่า VCC")


def calculate(vcc, r1, r2, rc, re, beta, vbe) -> BiasResult:
    """Calculate the DC operating point of a voltage-divider bias circuit.

    Parameters are in SI units (V and Ohm). Raises ValueError for
    physically invalid inputs.
    """
    _validate(vcc, r1, r2, rc, re, beta, vbe)

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    warnings: List[str] = []

    if vth <= vbe:
        # Not enough base drive: the transistor is cut off. Report the
        # physically sensible "off" state instead of negative currents.
        ib = ic = ie = 0.0
        ve = 0.0
        vb = vth
        vc = vcc
        vce = vcc
        region = "cutoff"
        warnings.append(
            f"VTH = {vth:.3f} V ไม่มากกว่า VBE = {vbe:.3f} V: "
            "ทรานซิสเตอร์อยู่ในโหมด Cutoff ผลจากสมการ Forward-Active ใช้ไม่ได้"
        )
    else:
        ib = (vth - vbe) / (rth + (beta + 1) * re)
        ic = beta * ib
        ie = (beta + 1) * ib
        ve = ie * re
        vb = ve + vbe
        vc = vcc - ic * rc
        vce = vc - ve

        if vce < VCE_SAT:
            region = "saturation"
            warnings.append(
                f"VCE = {vce:.3f} V ต่ำกว่า VCE(sat) ≈ {VCE_SAT:.1f} V: "
                "ทรานซิสเตอร์อาจอยู่ในโหมด Saturation ผลจากสมการ Forward-Active ใช้ไม่ได้"
            )
        else:
            region = "forward-active"

    return BiasResult(
        vcc=vcc,
        r1=r1,
        r2=r2,
        rc=rc,
        re=re,
        beta=beta,
        vbe=vbe,
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
    )
