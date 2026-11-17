"""Flask web application for the BJT DC Bias lab (ENG29 2121 Lab 02).

Supports three bias topologies: voltage divider, fixed bias and emitter
bias, with selectable input resistance units and output voltage/current
units.

The web layer only parses/validates the HTTP form, converts units, calls
the engineering module and renders the result. All circuit physics lives
in ``dc_bias.py``.
"""

from __future__ import annotations

from flask import Flask, render_template, request

from dc_bias import calculate_by_type

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
}

DEFAULT_BIAS = "voltage-divider"

# Fields entered as resistance; their input unit is selectable.
RESISTOR_FIELDS = {"r1", "r2", "rc", "re", "rb"}

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


def parse_form(bias_key: str, form, resistance_factor: float, labels=None) -> dict:
    """Convert raw form strings into SI-unit keyword arguments."""
    spec = BIAS_TYPES[bias_key]
    if labels is None:
        labels = _field_labels(spec)
    values = {}
    for name, _label, _unit in spec["fields"]:
        value = _to_float(name, labels[name], form.get(name))
        if name in RESISTOR_FIELDS:
            value *= resistance_factor  # selected resistance unit -> Ohm
        values[name] = value
    return values


def _fmt(value, unit):
    return f"{value:.{unit['decimals']}f}"


def _display(result, unit_r, unit_i, unit_v) -> dict:
    """Pre-format numbers in the selected output units."""
    ru = RESISTANCE_UNITS[unit_r]
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
        display["vth"] = _fmt(result.vth * vu["factor"], vu)
        display["rth"] = _fmt(result.rth / ru["factor"], ru)
        display["runit"] = ru["symbol"]
    if result.rb is not None:
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

    unit_r = _resolve_unit(RESISTANCE_UNITS, request.values.get("unit_r"), DEFAULT_UNIT_R)
    unit_i = _resolve_unit(CURRENT_UNITS, request.values.get("unit_i"), DEFAULT_UNIT_I)
    unit_v = _resolve_unit(VOLTAGE_UNITS, request.values.get("unit_v"), DEFAULT_UNIT_V)
    resistance_factor = RESISTANCE_UNITS[unit_r]["factor"]

    form = dict(spec["defaults"])
    result = None
    display = None
    errors = []

    # Resolve the unit label for each input field.
    form_fields = []
    for name, label, unit in spec["fields"]:
        if name in RESISTOR_FIELDS:
            shown_unit = RESISTANCE_UNITS[unit_r]["symbol"]
        else:
            shown_unit = unit
        form_fields.append({"name": name, "label": label, "unit": shown_unit})

    labels = {
        field["name"]: f"{field['label']} ({field['unit']})"
        for field in form_fields
    }

    if request.method == "POST":
        form = {name: request.form.get(name, "") for name, _l, _u in spec["fields"]}
        try:
            values = parse_form(bias_key, request.form, resistance_factor, labels)
            result = calculate_by_type(bias_key, **values)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            display = _display(result, unit_r, unit_i, unit_v)

    return render_template(
        "index.html",
        form=form,
        form_fields=form_fields,
        result=result,
        display=display,
        errors=errors,
        bias_types={key: item["label"] for key, item in BIAS_TYPES.items()},
        bias_key=bias_key,
        spec=spec,
        schematic=spec["schematic"],
        unit_r=unit_r,
        unit_i=unit_i,
        unit_v=unit_v,
        unit_r_symbol=RESISTANCE_UNITS[unit_r]["symbol"],
        resistance_units=RESISTANCE_UNITS,
        current_units=CURRENT_UNITS,
        voltage_units=VOLTAGE_UNITS,
    )


if __name__ == "__main__":
    app.run(debug=True)
