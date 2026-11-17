# Design Note — Lab 03 BJT DC Bias Web App

## Scope

Build the smallest working Flask web application that computes the DC
operating point of a voltage-divider-biased BJT common-emitter stage.

In scope:

- Single bias topology: voltage-divider bias.
- Forward-active approximation (constant β, constant VBE).
- Inputs: VCC, R1, R2, RC, RE, β, VBE.
- Outputs: VB, VE, VC, VCE, IC (plus IB, IE, VTH, RTH).
- Input validation and out-of-region warnings.
- Automated tests and GitHub history.

Out of scope (future labs): AC small-signal, transient, Bode plots,
signal generator, interactive schematic, SPICE/ngspice, FET.

## Architecture

```
Browser form
    │  HTTP POST /
    ▼
app.py  (Flask routes, form parsing, kΩ→Ω conversion)
    │  Python call
    ▼
dc_bias.py  (pure engineering calculation, no HTML/HTTP)
    │  BiasResult
    ▼
templates/index.html  (Jinja rendering with units)
```

`static/style.css` handles presentation only.

## Key decisions

- **Separation of concerns:** the physics lives only in `dc_bias.py`, so
  changing an equation never requires editing the HTML.
- **SI units internally:** the engineering module works in V/Ω/A; the
  web layer converts resistor inputs from kΩ.
- **Explicit region flag:** `region` is one of `forward-active`,
  `saturation`, `cutoff`, so the UI can warn instead of silently
  reporting an invalid approximation.
