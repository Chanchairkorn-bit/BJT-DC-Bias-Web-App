# BJT DC Bias Web App & CE Amplifier Simulator — ENG29 2121 Lab 03 & 04

Flask web application that calculates the DC operating point and simulates the AC/transient behavior of a BJT Common-Emitter (CE) amplifier:

- **Lab 03 Analytical Bias Topologies:**
  - **Voltage-divider bias** ($R_1 / R_2$ at base, $R_E$ at emitter)
  - **Fixed bias** ($R_B$ from $V_{CC}$ to base, emitter grounded)
  - **Emitter bias** ($R_B$ from $V_{CC}$ to base + $R_E$ at emitter)
- **Lab 04 SPICE Simulation Engine (`ngspice`):**
  - **DC Operating Point (`.op`):** High-precision physical simulation ($V_B, V_E, V_C, V_{CE}, I_C, I_B, V_{BE}$)
  - **AC Frequency Response (`.ac`):** Full frequency sweep with responsive SVG Bode plot (magnitude in dB and phase in degrees, midband gain, $-3\text{ dB}$ cutoff frequencies $f_L, f_H$)
  - **Transient Analysis (`.tran`):** Time-domain waveform visualization of $V_{in}(t)$ and $V_{out}(t)$, showing signal amplification and $180^\circ$ phase inversion.
  - **Engineering Provenance:** Direct side-by-side comparison between Analytical (constant $\beta$, constant $V_{BE}$) and physical SPICE models (`Q2N3904`).

Repository: https://github.com/Chanchairkorn-bit/BJT-DC-Bias-Web-App

---

## What It Does

1. **Topologies & Modes:**
   - Tabs allow seamless switching between Analytical bias modes and the CE SPICE Simulator.
   - For SPICE simulation, users can select between **DC (`.op`)**, **AC (`.ac`)**, **Transient (`.tran`)**, or **All Modes**.
2. **Individual Resistor Unit Selectors:**
   - Every resistor ($R_1, R_2, R_C, R_E, R_B, R_L$) features independent unit selection ($\Omega$, $\text{k}\Omega$, $\text{M}\Omega$).
   - Output voltage and current units are user-selectable ($\text{V}, \text{mV}, \mu\text{V}$ and $\text{A}, \text{mA}, \mu\text{A}$).
3. **SPICE Engine Integration:**
   - Python invokes `ngspice` in batch mode via `subprocess.run` (without `shell=True`, isolated temporary directories, and timeout enforcement).
   - Results are parsed directly from ngspice output files and rendered as self-contained SVG plots.
4. **Validation & Error Handling:**
   - Rejects non-numeric, zero, or negative component values ($R \le 0$, $V_{CC} \le 0$, $\beta \le 0$) with friendly Thai error banners.
   - Never masks solver errors or fabricates traces.

---

## Project Structure

```
BJT-DC-Bias-Web-App/
├── app.py                      # Flask routes, form parsing, unit conversions
├── dc_bias.py                  # Pure analytical engineering calculations (Lab 03)
├── spice_engine.py             # ngspice adapter: netlist generator, batch runner, parser
├── templates/
│   ├── index.html              # Unified template for form, schematics, and results
│   └── partials/
│       ├── schematic_voltage_divider.html
│       ├── schematic_fixed.html
│       ├── schematic_emitter.html
│       └── schematic_ce_spice.html  # Complete CE amplifier schematic with Cin, Cout, RL
├── static/
│   └── style.css               # Responsive design, theme tokens, and chart styling
├── tests/
│   ├── test_dc_bias.py         # Analytical engine unit tests
│   ├── test_web.py             # Flask test-client tests for analytical modes
│   ├── test_spice.py           # ngspice runner, validation, and parsing tests
│   └── test_ce_web.py          # Integration tests for CE SPICE web simulation
├── docs/
│   ├── validation.md           # Acceptance test matrix (B1–B8) and provenance notes
│   ├── design-note.md
│   └── reflection.md
├── requirements.txt            # Flask dependency
├── AGENTS.md                   # Engineering provenance and AI guidelines
└── README.md
```

---

## Prerequisites & Installation

### 1. Python & Dependencies

```bash
# Clone the repository
git clone https://github.com/Chanchairkorn-bit/BJT-DC-Bias-Web-App.git
cd BJT-DC-Bias-Web-App

# Create virtual environment (optional)
python -m venv .venv
# Activate on Windows: .venv\Scripts\Activate.ps1
# Activate on Linux/macOS: source .venv/bin/activate

# Install Flask
python -m pip install -r requirements.txt
```

*(Note for Windows: If `python` opens the Microsoft Store, use the `py` launcher instead, e.g. `py -m pip install -r requirements.txt`)*

### 2. Installing `ngspice`

- **Windows:**
  - Download `ngspice-47_64.7z` from [SourceForge](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/47/).
  - Extract to `C:\Spice64` or `C:\Users\<User>\Spice64`.
  - Add `C:\Spice64\bin` to your system `PATH`.
  - Verify in terminal: `ngspice -v` or `ngspice_con -v`.
- **Ubuntu / Debian:**
  ```bash
  sudo apt-get update && sudo apt-get install -y ngspice
  ```
- **macOS (Homebrew):**
  ```bash
  brew install ngspice
  ```

---

## Running the Application

```bash
# Start Flask development server
python -m flask --app app run --debug
# or using py launcher:
py app.py
```

Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in any modern web browser.

---

## Running Automated Tests

Run the full test suite (59 test cases covering both Lab 03 and Lab 04):

```bash
python -m unittest discover -s tests -v
# or
py -m unittest discover tests
```

---

## Acceptance Verification (B1–B8)

Detailed verification logs, provenance data, and test evidence are documented in [docs/validation.md](docs/validation.md):
- **B1 (Regression):** All Lab 3 analytical topologies preserved (**PASS**)
- **B2 (DC SPICE):** Real `.op` run matching reference operating point (**PASS**)
- **B3 (Change RE):** Dynamic recalculation verified (**PASS**)
- **B4 (AC Bode):** Magnitude and phase curves verified (**PASS**)
- **B5 (Transient):** $180^\circ$ phase inversion and wave scaling verified (**PASS**)
- **B6 (Change Source):** Signal amplitude scaling verified (**PASS**)
- **B7 (Invalid Input):** Proper error rejection without server failure (**PASS**)
- **B8 (UI):** Responsive desktop and mobile layouts (**PASS**)
