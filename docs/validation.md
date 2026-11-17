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

## Additional topologies

### Fixed bias (`VCC=12, RB=470k, RC=2.2k, β=100, VBE=0.70`)

```
IB  = (12 - 0.70) / 470000      = 24.043 µA
IC  = 100 * IB                   = 2.404 mA
IE  = 101 * IB                   = 2.428 mA
VE  = 0 V                        (emitter grounded)
VB  = 0.700 V
VC  = 12 - IC * 2200             = 6.711 V
VCE = VC                         = 6.711 V
```

### Emitter bias (`VCC=12, RB=470k, RC=2.2k, RE=1k, β=100, VBE=0.70`)

```
IB  = (12 - 0.70) / (470000 + 101*1000) = 19.790 µA
IC  = 100 * IB                           = 1.979 mA
IE  = 101 * IB                           = 1.999 mA
VE  = IE * 1000                          = 1.999 V
VB  = 1.999 + 0.70                       = 2.699 V
VC  = 12 - IC * 2200                     = 7.646 V
VCE = VC - VE                            = 5.647 V
```

All three default operating points are forward-active, so the model
applies without warnings.

## Known limitations

- Constant β and constant VBE are approximations; real devices vary with
  current and temperature.
- The saturation warning uses a fixed VCE(sat) ≈ 0.2 V threshold.
- No temperature, Early effect, or load-line analysis in this lab.
