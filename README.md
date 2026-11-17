# BJT DC Bias Web App — ENG29 2121 Lab 03

Flask web application that calculates the DC operating point of a BJT
common-emitter amplifier for three bias topologies:

- **Voltage-divider bias** (R1/R2 at the base)
- **Fixed bias** (RB from VCC to the base, emitter grounded)
- **Emitter bias** (RB from VCC to the base + RE at the emitter)

All use the forward-active approximation with a constant beta and a
constant VBE.

Repository: https://github.com/Chanchairkorn-bit/BJT-DC-Bias-Web-App

Lab 03 extends the Lab 02 single-topology app: the original voltage-divider
result is unchanged, while **Fixed Bias** and **Emitter Bias** are added
and the result is verified in a real browser (OpenCode Browser Tools /
Playwright MCP) against hand-calculated reference values.

## What it does

- Tabs select the bias topology; the form and schematic change to match.
- **Selectable units** on every topology: each resistor input (R1, R2, RC,
  RE, RB) has its own Ω / kΩ / MΩ selector, while output voltage is shown
  in V / mV / µV and output current in A / mA / µA.
- The Python backend (`dc_bias.py`) computes the DC operating point.
- Results are rendered in the browser with the selected units.
- Invalid inputs (`R ≤ 0`, `β ≤ 0`, `VCC ≤ 0`, non-numeric) show a clear
  error instead of crashing.
- If the operating point leaves the forward-active region, a warning is
  shown and the result is not presented as trustworthy.

## Unit selection

**Each resistor has its own unit selector** next to its input, so one
branch can be entered in kΩ while another is in Ω or MΩ. The schematic
labels update to match the unit of each individual resistor.

Output units are chosen in the bar above the inputs:

| Quantity | Options | Default |
|----------|---------|---------|
| Each resistor (R1, R2, RC, RE, RB) | Ω, kΩ, MΩ | kΩ |
| Voltage (VB, VE, VC, VCE, VTH) | V, mV, µV | V |
| Current (IC, IE, IB) | A, mA, µA | mA |

Internally everything is still computed in SI units (V, Ω, A); the
selectors only change what you type and what is displayed. For example,
`R2 = 22 kΩ`, `R2 = 22000 Ω` and `R2 = 0.022 MΩ` all describe the same
circuit, and `RTH`/`RB` are reported in the unit chosen for `R1`/`RB`.

## Project structure

```
BJT-DC-Bias-Web-App/
├── app.py                    # Flask routes + bias metadata (HTTP layer)
├── dc_bias.py                # pure engineering calculations
├── templates/
│   ├── index.html            # Jinja form + results
│   └── partials/             # one schematic per bias topology
├── static/style.css          # presentation
├── tests/
│   ├── test_dc_bias.py       # engineering unit tests
│   └── test_web.py           # Flask test-client tests
├── docs/                     # design / validation / reflection notes
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

Common practice: `IE = (β + 1)·IB`, `IC = β·IB`, and a constant `VBE`.
All topologies assume the forward-active region.

### 1. Voltage-divider bias

| Quantity | Equation |
|----------|----------|
| VTH | VCC · R2 / (R1 + R2) |
| RTH | R1 · R2 / (R1 + R2) |
| IB  | (VTH − VBE) / (RTH + (β + 1) · RE) |
| VE  | IE · RE |
| VB  | VE + VBE |
| VC  | VCC − IC · RC |
| VCE | VC − VE |

### 2. Fixed bias

| Quantity | Equation |
|----------|----------|
| IB  | (VCC − VBE) / RB |
| IE  | (β + 1) · IB |
| VB  | VBE |
| VE  | 0 (emitter grounded) |
| VC  | VCC − IC · RC |
| VCE | VC |

### 3. Emitter bias

| Quantity | Equation |
|----------|----------|
| IB  | (VCC − VBE) / (RB + (β + 1) · RE) |
| IE  | (β + 1) · IB |
| VE  | IE · RE |
| VB  | VE + VBE |
| VC  | VCC − IC · RC |
| VCE | VC − VE |

This is **not** a SPICE/ngspice solver. Outside the forward-active
region (cutoff when `VTH ≤ VBE`, or saturation when `VCE` approaches the
saturation voltage) the app shows a warning.

## Reference examples

### Voltage-divider bias (default)

Inputs: `VCC = 12 V`, `R1 = 100 kΩ`, `R2 = 22 kΩ`, `RC = 2.2 kΩ`,
`RE = 1 kΩ`, `β = 100`, `VBE = 0.70 V`.

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

### Fixed bias (default)

Inputs: `VCC = 12 V`, `RB = 470 kΩ`, `RC = 2.2 kΩ`, `β = 100`,
`VBE = 0.70 V`.

| Quantity | Value |
|----------|-------|
| IB  | 24.043 µA |
| IC  | 2.404 mA |
| IE  | 2.428 mA |
| VB  | 0.700 V |
| VE  | 0.000 V |
| VC  | 6.711 V |
| VCE | 6.711 V |

### Emitter bias (default)

Inputs: `VCC = 12 V`, `RB = 470 kΩ`, `RC = 2.2 kΩ`, `RE = 1 kΩ`,
`β = 100`, `VBE = 0.70 V`.

| Quantity | Value |
|----------|-------|
| IB  | 19.790 µA |
| IC  | 1.979 mA |
| IE  | 1.999 mA |
| VB  | 2.699 V |
| VE  | 1.999 V |
| VC  | 7.646 V |
| VCE | 5.647 V |

## Notes

- Flask's debug server is for local development only.
- Do not commit `.venv/`, `.env`, API keys or credentials.
