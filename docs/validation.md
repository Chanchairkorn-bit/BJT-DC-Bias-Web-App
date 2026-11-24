# Validation — Lab 03 & Lab 04 BJT Amplifier Simulator

---

## Part 1: Lab 03 Analytical Reference Validation

### Independent reference calculation
Using the lab values `VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V`:

```
VTH = 12 * 22000 / (100000 + 22000)      = 2.1639 V
RTH = 100000 * 22000 / (100000 + 22000)  = 18032.79 Ω
IB  = (2.1639 - 0.70) / (18032.79 + 101*1000)
    = 1.4639 / 119032.79                 = 12.2986 µA
IC  = 100 * IB                            = 1.2299 mA
IE  = 101 * IB                            = 1.2422 mA
VE  = 1.2422e-3 * 1000                    = 1.2422 V
VB  = 1.2422 + 0.70                       = 1.9422 V
VC  = 12 - 1.2299e-3 * 2200               = 9.2943 V
VCE = 9.2943 - 1.2422                     = 8.0522 V
```

`VCE = 8.05 V` is well above the saturation voltage, confirming forward-active operation.

---

## Part 2: Lab 04 SPICE Simulation Validation (B1–B8)

### Simulation Engine & Model Specifications
- **SPICE Engine:** `ngspice-47` (Compiled with KLU / Sparse Direct Linear Solver)
- **Execution Mode:** Batch mode (`ngspice_con -b`) via isolated temporary directories with timeout enforcement
- **Transistor Model:** `Q2N3904 NPN`
  ```spice
  .model Q2N3904 NPN (Is=1E-14 Bf=100 Vaf=100 Ikf=0.1 Xtb=1.5 Br=4 Cjc=4pF Cje=8pF Tr=30n Tf=400p)
  ```

### Acceptance Test Matrix (B1–B8)

| Case | Test Description | Method | Input Fixture | Expected / Reference | Observed from Engine | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **B1** | **Regression:** Lab 3 Three Analytical Modes | Automated test suite (`test_web.py`, `test_dc_bias.py`) | Voltage-Divider, Fixed Bias, Emitter Bias reference inputs | Identical hand-calculation results across all 3 modes | All 46 Lab 3 tests pass without modification | **PASS** |
| **B2** | **DC SPICE:** Reference CE Voltage Divider | `spice_engine.run_simulation(..., mode="dc")` & web client | `VCC=12V, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100` | Real ngspice `.op` operating point: `VB≈1.95V, VE≈1.29V, VC≈9.19V, IC≈1.28mA` | `VB=1.947 V, VE=1.287 V, VC=9.195 V, VCE=7.908 V, IC=1.275 mA, IB=12.03 µA`. Provenance side-by-side displayed. | **PASS** |
| **B3** | **Change RE:** Dynamic Operating Point & Gain | Change single parameter `RE` from `1 kΩ` to `2 kΩ` | `RE=2 kΩ`, all other parameters unchanged | Operating point and gain must dynamically adapt | `VE` increased from 1.287 V to 1.488 V; `IC` decreased from 1.275 mA to 0.744 mA. Results confirm real solver execution. | **PASS** |
| **B4** | **AC Response:** Bode Plot Magnitude & Phase | `.ac dec 20 1 100Meg` frequency sweep | `Cin=10µF, Cout=10µF, RL=10k, RC=2.2k, RE=1k` | Midband Gain $|A_v| \approx (R_C \parallel R_L) / R_E \approx 1.8 \approx 5.1\text{ dB}$, with low-f & high-f roll-off | Midband gain: **4.84 dB** (1.75x linear). Lower cutoff $f_L \approx 10\text{ Hz}$, Upper cutoff $f_H \approx 32.8\text{ MHz}$. Responsive Bode plot generated. | **PASS** |
| **B5** | **Transient Response:** Waveform & Phase Inversion | `.tran` time-domain analysis | $V_{in} = 10\text{ mV}$ peak at $1\text{ kHz}$ | $V_{out} \approx 17.5\text{ mV}$ peak, exactly $180^\circ$ out-of-phase with $V_{in}$ | $V_{in,\text{peak}} = 10.0\text{ mV}$, $V_{out,\text{peak}} = 17.5\text{ mV}$, Observed $|A_v| = 1.75\text{x}$. Phase inversion confirmed ($180^\circ$). | **PASS** |
| **B6** | **Change Source:** Waveform Scaling | Scale input amplitude from $10\text{ mV}$ to $20\text{ mV}$ | $V_{in} = 20\text{ mV}$ peak at $1\text{ kHz}$ | Waveform amplitude must scale proportionally ($V_{out} \approx 35\text{ mV}$) | Observed $V_{out,\text{peak}} = 34.9\text{ mV}$, observed $|A_v| = 1.75\text{x}$. Graph dynamically updates. | **PASS** |
| **B7** | **Invalid / Error Handling:** Reject Illegal Inputs | Submit `RE = 0` or negative parameters | `RE = 0 Ω` | Clear validation error message; no solver crash; no false success | Form displays: `"ค่า RE ต้องมากกว่า 0 (RE must be positive > 0 Ω)"`. Server returns HTTP 200 with error banner. | **PASS** |
| **B8** | **UI & Responsiveness:** Desktop and Mobile Inspection | Browser inspection at 1280px (Desktop) and 390px (Mobile) | Viewport resize and tab navigation | Readable forms, schematics, statistics, charts, and tables | Layout adapts cleanly: 2-column grid on desktop, single-column stack on mobile. Charts scroll horizontally if required. | **PASS** |

---

## Part 3: Engineering Provenance (SPICE vs. Analytical)

| Quantity | Analytical (Lab 03) | ngspice-47 (.op) | Difference ($\Delta$) | Physical Reason for Difference |
| :--- | :--- | :--- | :--- | :--- |
| **$V_B$** | 1.942 V | 1.947 V | $+0.005\text{ V}$ ($+0.26\%$) | ngspice models finite base-collector leakage and dynamic base resistance ($R_B$). |
| **$V_E$** | 1.242 V | 1.287 V | $+0.045\text{ V}$ ($+3.62\%$) | Analytical assumes fixed $V_{BE} = 0.70\text{ V}$, while ngspice calculates physical $V_{BE} = 0.6599\text{ V}$ from diode law $I_C = I_S \exp(V_{BE}/V_T)$. |
| **$V_C$** | 9.294 V | 9.195 V | $-0.099\text{ V}$ ($-1.07\%$) | Slightly higher actual collector current ($I_C$) produces greater voltage drop across $R_C$. |
| **$V_{CE}$** | 8.052 V | 7.908 V | $-0.144\text{ V}$ ($-1.79\%$) | $V_{CE} = V_C - V_E$ reflects both higher $V_E$ and lower $V_C$. |
| **$I_C$** | 1.230 mA | 1.275 mA | $+0.045\text{ mA}$ ($+3.66\%$) | Consequence of dynamic $V_{BE} \approx 0.66\text{ V}$ leaving higher voltage across $R_E$. |
| **$I_B$** | 12.30 µA | 12.03 µA | $-0.27\text{ µA}$ ($-2.20\%$) | Non-ideal base current recombination and Early effect ($V_{AF} = 100\text{ V}$). |

---

## Part 4: Automated Test Execution

All 59 automated test cases pass:

```bash
python -m unittest discover -s tests -v
```

Summary:
- `tests/test_dc_bias.py`: 19 tests (analytical engine) — **PASS**
- `tests/test_web.py`: 27 tests (Flask web routes & unit selection) — **PASS**
- `tests/test_spice.py`: 8 tests (ngspice adapter, validation, OP/AC/TRAN) — **PASS**
- `tests/test_ce_web.py`: 5 tests (CE simulator HTTP routes & integration) — **PASS**
- **Total: 59 passed, 0 failed, 0 errors** in 0.44s.
