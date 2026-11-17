# Reflection — Lab 03 BJT DC Bias Web App

## What was built

A multi-file Flask application that separates the HTTP layer (`app.py`),
the engineering logic (`dc_bias.py`), the template
(`templates/index.html`), presentation (`static/style.css`) and tests
(`tests/`).

## What I learned

- Opening `templates/index.html` directly is not the same as running
  Flask: without the server, the form has nowhere to send the input and
  no Python code runs.
- The form sends the field values in an HTTP POST; Flask reads them via
  `request.form`, converts units, and calls the engineering function.
- Because the equations live only in `dc_bias.py`, changing a formula
  does not require touching the HTML — the template just displays the
  computed values.
- The forward-active approximation is only valid inside its region. When
  the circuit is in cutoff or saturation, the app must warn the user
  instead of presenting the numbers as accurate.

## Improvements for next labs

- Add more bias topologies (fixed bias, emitter bias).
- Add a DC load line and graph.
- Compare with ngspice results.
- Add AC small-signal gain and Bode plots.
