"""Flask web application for the BJT DC Bias lab (ENG29 2121 Lab 03).

Supports three bias topologies: voltage divider, fixed bias and emitter
bias. Every resistor input has its own unit selector (ohm, kOhm, MOhm),
and the output voltage/current units are selectable as well.

The web layer only parses/validates the HTTP form, converts units, calls
the engineering module and renders the result. All circuit physics lives
in ``dc_bias.py``.
"""

from __future__ import annotations

from flask import Flask, render_template, request

from dc_bias import calculate_by_type
from spice_engine import CircuitParams, run_simulation

app = Flask(__name__)

# Metadata for each supported bias topology. ``fields`` drives both the
# form rendering and the request parsing, so adding a field only requires
# editing this table.
BIAS_TYPES = {
    "voltage-divider": {
        "label": "Voltage Divider",
        "title": "Voltage-Divider Bias",
        "schematic": "partials/schematic_voltage_divider.html",
        "fields": [
            ("vcc", "VCC", "V"),
            ("r1", "R1", "kΩ"),
            ("r2", "R2", "kΩ"),
            ("rc", "RC", "kΩ"),
            ("re", "RE", "kΩ"),
            ("beta", "β", "beta"),
            ("vbe", "VBE", "V"),
        ],
        "defaults": {
            "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
            "re": "1", "beta": "100", "vbe": "0.70",
        },
    },
    "fixed": {
        "label": "Fixed Bias",
        "title": "Fixed Bias",
        "schematic": "partials/schematic_fixed.html",
        "fields": [
            ("vcc", "VCC", "V"),
            ("rb", "RB", "kΩ"),
            ("rc", "RC", "kΩ"),
            ("beta", "β", "beta"),
            ("vbe", "VBE", "V"),
        ],
        "defaults": {
            "vcc": "12", "rb": "470", "rc": "2.2", "beta": "100", "vbe": "0.70",
        },
    },
    "emitter": {
        "label": "Emitter Bias",
        "title": "Emitter Bias",
        "schematic": "partials/schematic_emitter.html",
        "fields": [
            ("vcc", "VCC", "V"),
            ("rb", "RB", "kΩ"),
            ("rc", "RC", "kΩ"),
            ("re", "RE", "kΩ"),
            ("beta", "β", "beta"),
            ("vbe", "VBE", "V"),
        ],
        "defaults": {
            "vcc": "12", "rb": "470", "rc": "2.2", "re": "1",
            "beta": "100", "vbe": "0.70",
        },
    },
    "ce-amplifier": {
        "label": "CE SPICE Simulator (Lab 04)",
        "title": "Common-Emitter Amplifier SPICE Simulator",
        "schematic": "partials/schematic_ce_spice.html",
        "fields": [
            ("vcc", "VCC", "V"),
            ("r1", "R1", "kΩ"),
            ("r2", "R2", "kΩ"),
            ("rc", "RC", "kΩ"),
            ("re", "RE", "kΩ"),
            ("rl", "RL", "kΩ"),
            ("cin", "Cin", "µF"),
            ("cout", "Cout", "µF"),
            ("beta", "β", "beta"),
            ("amplitude", "Vin (Peak)", "mV"),
            ("frequency", "Frequency", "Hz"),
        ],
        "defaults": {
            "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1",
            "rl": "10", "cin": "10", "cout": "10", "beta": "100",
            "amplitude": "10", "frequency": "1000",
        },
    },
}

DEFAULT_BIAS = "voltage-divider"

# Fields entered as resistance; each one has its own unit selector.
RESISTOR_FIELDS = {"r1", "r2", "rc", "re", "rb", "rl"}

RESISTANCE_UNITS = {
    "ohm": {"symbol": "Ω", "factor": 1.0, "decimals": 3},
    "kohm": {"symbol": "kΩ", "factor": 1e3, "decimals": 3},
    "mohm": {"symbol": "MΩ", "factor": 1e6, "decimals": 6},
}

CURRENT_UNITS = {
    "a": {"symbol": "A", "factor": 1.0, "decimals": 6},
    "ma": {"symbol": "mA", "factor": 1e3, "decimals": 3},
    "ua": {"symbol": "µA", "factor": 1e6, "decimals": 3},
}

VOLTAGE_UNITS = {
    "v": {"symbol": "V", "factor": 1.0, "decimals": 3},
    "mv": {"symbol": "mV", "factor": 1e3, "decimals": 3},
    "uv": {"symbol": "µV", "factor": 1e6, "decimals": 3},
}

DEFAULT_UNIT_R = "kohm"
DEFAULT_UNIT_I = "ma"
DEFAULT_UNIT_V = "v"


def _resolve_unit(table, key, default):
    return key if key in table else default


def _unit_field_name(name: str) -> str:
    """Form control name of the unit selector for resistor ``name``."""
    return f"unit_{name}"


def _field_labels(spec) -> dict:
    return {name: f"{label} ({unit})" for name, label, unit in spec["fields"]}


def _to_float(name: str, label: str, raw: str) -> float:
    raw = (raw or "").strip()
    if raw == "":
        raise ValueError(f"กรุณากรอกค่า {label}")
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"ค่า {label} ต้องเป็นตัวเลข")


def parse_form(bias_key: str, form, resistance_factors, labels=None) -> dict:
    """Convert raw form strings into SI-unit keyword arguments.

    ``resistance_factors`` maps each resistor field name (``r1``, ``rc`` …)
    to the factor of the unit selected for that individual field.
    """
    spec = BIAS_TYPES[bias_key]
    if labels is None:
        labels = _field_labels(spec)
    values = {}
    for name, _label, _unit in spec["fields"]:
        value = _to_float(name, labels[name], form.get(name))
        if name in RESISTOR_FIELDS:
            value *= resistance_factors[name]  # that field's unit -> Ohm
        values[name] = value
    return values


def _fmt(value, unit):
    return f"{value:.{unit['decimals']}f}"


def _display(result, unit_i, unit_v, rth_unit=DEFAULT_UNIT_R, rb_unit=DEFAULT_UNIT_R) -> dict:
    """Pre-format numbers in the selected output units."""
    iu = CURRENT_UNITS[unit_i]
    vu = VOLTAGE_UNITS[unit_v]

    display = {
        "vunit": vu["symbol"],
        "iunit": iu["symbol"],
        "vb": _fmt(result.vb * vu["factor"], vu),
        "ve": _fmt(result.ve * vu["factor"], vu),
        "vc": _fmt(result.vc * vu["factor"], vu),
        "vce": _fmt(result.vce * vu["factor"], vu),
        "ic": _fmt(result.ic * iu["factor"], iu),
        "ie": _fmt(result.ie * iu["factor"], iu),
        "ib": _fmt(result.ib * iu["factor"], iu),
    }
    if result.vth is not None:
        ru = RESISTANCE_UNITS[rth_unit]
        display["vth"] = _fmt(result.vth * vu["factor"], vu)
        display["rth"] = _fmt(result.rth / ru["factor"], ru)
        display["runit"] = ru["symbol"]
    if result.rb is not None:
        ru = RESISTANCE_UNITS[rb_unit]
        display["rb"] = _fmt(result.rb / ru["factor"], ru)
        display["runit"] = ru["symbol"]
    return display


@app.route("/", methods=["GET", "POST"])
def index():
    bias_key = (
        request.values.get("bias_type")
        or request.args.get("bias")
        or DEFAULT_BIAS
    )
    if bias_key not in BIAS_TYPES:
        bias_key = DEFAULT_BIAS
    spec = BIAS_TYPES[bias_key]

    unit_i = _resolve_unit(CURRENT_UNITS, request.values.get("unit_i"), DEFAULT_UNIT_I)
    unit_v = _resolve_unit(VOLTAGE_UNITS, request.values.get("unit_v"), DEFAULT_UNIT_V)
    # ``unit_r`` is only a fallback default; each resistor may override it
    # with its own ``unit_<field>`` selector.
    default_unit_r = _resolve_unit(
        RESISTANCE_UNITS, request.values.get("unit_r"), DEFAULT_UNIT_R
    )

    form = dict(spec["defaults"])
    result = None
    display = None
    errors = []
    analysis_mode = request.values.get("analysis_mode", "dc")
    spice_result = None

    # Resolve the unit of every input field.
    form_fields = []
    resistor_units = {}
    for name, label, unit in spec["fields"]:
        if name in RESISTOR_FIELDS:
            unit_key = _unit_field_name(name)
            chosen = _resolve_unit(
                RESISTANCE_UNITS, request.values.get(unit_key), default_unit_r
            )
            resistor_units[name] = chosen
            form_fields.append(
                {
                    "name": name,
                    "label": label,
                    "unit": RESISTANCE_UNITS[chosen]["symbol"],
                    "unit_name": unit_key,
                    "unit_key": chosen,
                }
            )
        else:
            form_fields.append(
                {
                    "name": name,
                    "label": label,
                    "unit": unit,
                    "unit_name": None,
                    "unit_key": None,
                }
            )

    labels = {
        field["name"]: f"{field['label']} ({field['unit']})"
        for field in form_fields
    }
    resistance_factors = {
        name: RESISTANCE_UNITS[key]["factor"]
        for name, key in resistor_units.items()
    }

    if request.method == "POST":
        form = {name: request.form.get(name, "") for name, _l, _u in spec["fields"]}
        try:
            values = parse_form(bias_key, request.form, resistance_factors, labels)
            if bias_key == "ce-amplifier":
                cp = CircuitParams(
                    vcc=values["vcc"],
                    r1=values["r1"],
                    r2=values["r2"],
                    rc=values["rc"],
                    re=values["re"],
                    rl=values.get("rl", 10_000.0),
                    cin=values.get("cin", 10.0) * 1e-6,
                    cout=values.get("cout", 10.0) * 1e-6,
                    beta=values.get("beta", 100.0),
                    amplitude=values.get("amplitude", 10.0) * 1e-3,
                    frequency=values.get("frequency", 1000.0),
                )
                spice_result = run_simulation(cp, mode=analysis_mode)
                if spice_result.get("status") == "error":
                    errors.extend(spice_result.get("errors", ["Simulation failed"]))
                else:
                    if "dc" in spice_result:
                        dc_raw = spice_result["dc"]
                        vu = VOLTAGE_UNITS[unit_v]
                        iu = CURRENT_UNITS[unit_i]
                        spice_result["display"] = {
                            "vb": _fmt(dc_raw["vb"] * vu["factor"], vu),
                            "ve": _fmt(dc_raw["ve"] * vu["factor"], vu),
                            "vc": _fmt(dc_raw["vc"] * vu["factor"], vu),
                            "vce": _fmt(dc_raw["vce"] * vu["factor"], vu),
                            "ic": _fmt(dc_raw["ic"] * iu["factor"], iu),
                            "ib": _fmt(dc_raw["ib"] * iu["factor"], iu),
                            "vbe": _fmt(dc_raw["vbe"] * vu["factor"], vu),
                            "vunit": vu["symbol"],
                            "iunit": iu["symbol"],
                        }
                    try:
                        result = calculate_by_type(
                            "voltage-divider",
                            vcc=values["vcc"],
                            r1=values["r1"],
                            r2=values["r2"],
                            rc=values["rc"],
                            re=values["re"],
                            beta=values["beta"],
                            vbe=0.70,
                        )
                        display = _display(
                            result,
                            unit_i,
                            unit_v,
                            rth_unit=resistor_units.get("r1", default_unit_r),
                            rb_unit=resistor_units.get("rb", default_unit_r),
                        )
                    except Exception:
                        pass
            else:
                result = calculate_by_type(bias_key, **values)
                display = _display(
                    result,
                    unit_i,
                    unit_v,
                    rth_unit=resistor_units.get("r1", default_unit_r),
                    rb_unit=resistor_units.get("rb", default_unit_r),
                )
        except ValueError as exc:
            errors.append(str(exc))

    # Schematic labels follow the unit chosen for each individual resistor.
    unit_r_symbols = {
        f"unit_{name}_symbol": RESISTANCE_UNITS[key]["symbol"]
        for name, key in resistor_units.items()
    }

    return render_template(
        "index.html",
        form=form,
        form_fields=form_fields,
        result=result,
        display=display,
        spice_result=spice_result,
        analysis_mode=analysis_mode,
        errors=errors,
        bias_types={key: item["label"] for key, item in BIAS_TYPES.items()},
        bias_key=bias_key,
        spec=spec,
        schematic=spec["schematic"],
        unit_i=unit_i,
        unit_v=unit_v,
        current_units=CURRENT_UNITS,
        voltage_units=VOLTAGE_UNITS,
        resistance_units=RESISTANCE_UNITS,
        **unit_r_symbols,
    )


if __name__ == "__main__":
    app.run(debug=True)
