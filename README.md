# BJT DC Bias Web App — ENG29 2121 Lab 02

Flask web application that calculates the DC operating point of a BJT
common-emitter amplifier using **voltage-divider bias** with the
forward-active approximation.

Repository: https://github.com/Chanchairkorn-bit/BJT-DC-Bias-Web-App

## What it does

- Web form accepts `VCC`, `R1`, `R2`, `RC`, `RE`, `β (beta)` and `VBE`.
- Resistors are entered in **kΩ** and converted to Ω before calculating.
- The Python backend (`dc_bias.py`) computes `VTH`, `RTH`, `IB`, `IC`,
  `IE`, `VB`, `VE`, `VC` and `VCE`.
- Results are rendered in the browser with units.
- Invalid inputs (`R ≤ 0`, `β ≤ 0`, `VCC ≤ 0`, non-numeric) show a clear
  error instead of crashing.
- If the operating point leaves the forward-active region, a warning is
  shown and the result is not presented as trustworthy.

## Project structure

```
BJT-DC-Bias-Web-App/
├── app.py                 # Flask routes (HTTP layer)
├── dc_bias.py             # pure engineering calculations
├── templates/index.html   # Jinja form + results
├── static/style.css       # presentation
├── tests/
│   ├── test_dc_bias.py    # engineering unit tests
│   └── test_web.py        # Flask test-client tests
├── docs/                  # design / validation / reflection notes
├── requirements.txt
└── README.md
```

## Install and run

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Run the development server
python -m flask --app app run --debug
```

Open <http://127.0.0.1:5000/> in a browser.

> **Windows note:** if `python` opens the Microsoft Store instead of
> running Python, use the `py` launcher instead, for example
> `py -m venv .venv` and `py -m pip install -r requirements.txt`.

> The app must be run through the Flask server. Opening
> `templates/index.html` directly (`file://`) does **not** work because
> the calculation happens in Python, not in the HTML file.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Engineering model

Forward-active approximation with constant `β` and constant `VBE`:

| Quantity | Equation |
|----------|----------|
| VTH | VCC · R2 / (R1 + R2) |
| RTH | R1 · R2 / (R1 + R2) |
| IB  | (VTH − VBE) / (RTH + (β + 1) · RE) |
| IC  | β · IB |
| IE  | (β + 1) · IB |
| VE  | IE · RE |
| VB  | VE + VBE |
| VC  | VCC − IC · RC |
| VCE | VC − VE |

This is **not** a SPICE/ngspice solver. Outside the forward-active
region (cutoff when `VTH ≤ VBE`, or saturation when `VCE` approaches the
saturation voltage) the app shows a warning.

## Reference example

Inputs: `VCC = 12 V`, `R1 = 100 kΩ`, `R2 = 22 kΩ`, `RC = 2.2 kΩ`,
`RE = 1 kΩ`, `β = 100`, `VBE = 0.70 V`.

Expected result (forward-active):

| Quantity | Value |
|----------|-------|
| VTH | 2.164 V |
| RTH | 18.033 kΩ |
| IB  | 12.30 µA |
| IC  | 1.230 mA |
| IE  | 1.242 mA |
| VB  | 1.942 V |
| VE  | 1.242 V |
| VC  | 9.294 V |
| VCE | 8.052 V |

## Notes

- Flask's debug server is for local development only.
- Do not commit `.venv/`, `.env`, API keys or credentials.
