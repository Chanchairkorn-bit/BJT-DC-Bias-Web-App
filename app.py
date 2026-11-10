"""Flask web application for the BJT DC Bias lab (ENG29 2121 Lab 02).

The web layer only parses/validates the HTTP form, converts resistor
values from kOhm to Ohm, calls the engineering module and renders the
result. All circuit physics lives in ``dc_bias.py``.
"""

from __future__ import annotations

from flask import Flask, render_template, request

from dc_bias import calculate

app = Flask(__name__)

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

# Sensible starting values from the lab handout.
DEFAULT_FORM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}

FIELD_LABELS = {
    "vcc": "VCC (V)",
    "r1": "R1 (kΩ)",
    "r2": "R2 (kΩ)",
    "rc": "RC (kΩ)",
    "re": "RE (kΩ)",
    "beta": "β (beta)",
    "vbe": "VBE (V)",
}


def _to_float(name: str, raw: str) -> float:
    """Parse a form field into float or raise a readable ValueError."""
    raw = (raw or "").strip()
    if raw == "":
        raise ValueError(f"กรุณากรอกค่า {FIELD_LABELS[name]}")
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"ค่า {FIELD_LABELS[name]} ต้องเป็นตัวเลข")


def parse_form(form) -> dict:
    """Convert raw form strings into SI-unit keyword arguments."""
    vcc = _to_float("vcc", form.get("vcc"))
    # Resistors are entered in kOhm; convert to Ohm before calculating.
    r1 = _to_float("r1", form.get("r1")) * 1000.0
    r2 = _to_float("r2", form.get("r2")) * 1000.0
    rc = _to_float("rc", form.get("rc")) * 1000.0
    re = _to_float("re", form.get("re")) * 1000.0
    beta = _to_float("beta", form.get("beta"))
    vbe = _to_float("vbe", form.get("vbe"))
    return {
        "vcc": vcc,
        "r1": r1,
        "r2": r2,
        "rc": rc,
        "re": re,
        "beta": beta,
        "vbe": vbe,
    }


def _display(result) -> dict:
    """Pre-format numbers (with units) for the template."""
    return {
        "vb": f"{result.vb:.3f}",
        "ve": f"{result.ve:.3f}",
        "vc": f"{result.vc:.3f}",
        "vce": f"{result.vce:.3f}",
        "ic_ma": f"{result.ic * 1000.0:.3f}",
        "ie_ma": f"{result.ie * 1000.0:.3f}",
        "ib_ua": f"{result.ib * 1e6:.3f}",
        "vth": f"{result.vth:.3f}",
        "rth_kohm": f"{result.rth / 1000.0:.3f}",
    }


@app.route("/", methods=["GET", "POST"])
def index():
    form = dict(DEFAULT_FORM)
    result = None
    display = None
    errors = []

    if request.method == "POST":
        form = {name: request.form.get(name, "") for name in FIELDS}
        try:
            values = parse_form(request.form)
            result = calculate(**values)
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
    )


if __name__ == "__main__":
    app.run(debug=True)
