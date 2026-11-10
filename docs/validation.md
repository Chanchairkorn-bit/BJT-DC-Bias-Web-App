# Validation — Lab 02 BJT DC Bias Web App

## Independent reference calculation

Using the lab values `VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ,
RE=1 kΩ, β=100, VBE=0.70 V`:

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

`VCE = 8.05 V` is well above the saturation voltage, so the device is
in the forward-active region and the approximation is valid.

## Automated tests

| Test | Check |
|------|-------|
| `test_thevenin` | VTH and RTH match the hand calculation |
| `test_currents` | IB, IC, IE match within tolerance |
| `test_voltages` | VB, VE, VC, VCE match within tolerance |
| `test_region_is_forward_active` | Region is forward-active, no warnings |
| `test_zero_resistor_rejected` | R ≤ 0 raises ValueError |
| `test_zero_beta_rejected` | β ≤ 0 raises ValueError |
| `test_negative_vcc_rejected` | VCC ≤ 0 raises ValueError |
| `test_cutoff_warning` | VTH ≤ VBE → cutoff + warning |
| `test_saturation_warning` | VCE below VCE(sat) → saturation + warning |
| `test_get_index_shows_form` | GET / returns 200 with form |
| `test_post_valid_input_computes_result` | POST / returns computed values |
| `test_post_non_numeric_shows_error` | Non-numeric input shows error, no crash |
| `test_post_zero_resistor_shows_error` | Zero resistor shows error, no crash |

Run with:

```bash
python -m unittest discover -s tests -v
```

## Known limitations

- Constant β and constant VBE are approximations; real devices vary with
  current and temperature.
- The saturation warning uses a fixed VCE(sat) ≈ 0.2 V threshold.
- No temperature, Early effect, or load-line analysis in this lab.
