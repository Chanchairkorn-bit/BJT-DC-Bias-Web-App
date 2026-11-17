"""Flask web application for the BJT DC Bias lab (ENG29 2121 Lab 02).

Supports three bias topologies: voltage divider, fixed bias and emitter
bias. The web layer only parses/validates the HTTP form, converts
resistor values from kOhm to Ohm, calls the engineering module and
renders the result. All circuit physics lives in ``dc_bias.py``.
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

# Fields entered in kOhm that must be converted to Ohm before calculating.
RESISTOR_FIELDS = {"r1", "r2", "rc", "re", "rb"}


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


def parse_form(bias_key: str, form) -> dict:
    """Convert raw form strings into SI-unit keyword arguments."""
    spec = BIAS_TYPES[bias_key]
    labels = _field_labels(spec)
    values = {}
    for name, _label, _unit in spec["fields"]:
        value = _to_float(name, labels[name], form.get(name))
        if name in RESISTOR_FIELDS:
            value *= 1000.0  # kOhm -> Ohm
        values[name] = value
    return values


def _display(result) -> dict:
    """Pre-format numbers (with units) for the template."""
    display = {
        "vb": f"{result.vb:.3f}",
        "ve": f"{result.ve:.3f}",
        "vc": f"{result.vc:.3f}",
        "vce": f"{result.vce:.3f}",
        "ic_ma": f"{result.ic * 1000.0:.3f}",
        "ie_ma": f"{result.ie * 1000.0:.3f}",
        "ib_ua": f"{result.ib * 1e6:.3f}",
    }
    if result.vth is not None:
        display["vth"] = f"{result.vth:.3f}"
        display["rth_kohm"] = f"{result.rth / 1000.0:.3f}"
    if result.rb is not None:
        display["rb_kohm"] = f"{result.rb / 1000.0:.3f}"
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

    form = dict(spec["defaults"])
    result = None
    display = None
    errors = []

    if request.method == "POST":
        form = {name: request.form.get(name, "") for name, _l, _u in spec["fields"]}
        try:
            values = parse_form(bias_key, request.form)
            result = calculate_by_type(bias_key, **values)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            display = _display(result)

    return render_template(
        "index.html",
        form=form,
        result=result,
        display=display,
        errors=errors,
        bias_types={key: item["label"] for key, item in BIAS_TYPES.items()},
        bias_key=bias_key,
        spec=spec,
        schematic=spec["schematic"],
    )


if __name__ == "__main__":
    app.run(debug=True)
