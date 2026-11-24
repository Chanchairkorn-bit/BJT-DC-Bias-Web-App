# AGENTS.md — Coding conventions for this project

## Purpose

Flask web app that computes the BJT voltage-divider DC bias operating point (Lab 03) and simulates the Common-Emitter Transistor Amplifier using `ngspice` (Lab 04) for ENG29 2121.

## Rules

- **Separation of Concerns:**
  - Analytical math belongs in `dc_bias.py` only. No web framework imports.
  - External simulation logic belongs in `spice_engine.py` only.
  - Web routes, HTTP validation, and unit conversions belong in `app.py`.
- **Subprocess Safety:**
  - Always invoke `ngspice` via `subprocess.run` with list arguments (never `shell=True`).
  - Enforce timeout limits and run in isolated temporary working directories.
- **Input Validation & Provenance:**
  - Internal units are SI (V, Ω, A, F, Hz).
  - Convert selected units (Ω, kΩ, MΩ, mV, µA, etc.) cleanly at the web boundary.
  - Clearly distinguish between analytical approximations (constant β, constant VBE) and SPICE simulation outputs (physical Gummel-Poon model).
  - Never fabricate simulation traces or hard-code mock values.
- **Testing & Stability:**
  - Every new engineering function or route must have automated tests under `tests/`.
  - Maintain 100% regression compatibility for existing Lab 03 tests.
  - Reject invalid inputs (non-numeric, ≤ 0) with clear, human-readable error messages.
- **Repository Cleanliness:**
  - Do not commit `.venv/`, `.env`, build artifacts, large temporary logs, or binary archives to Git.

## Commands

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run application
python -m flask --app app run --debug

# Run all test suites
python -m unittest discover -s tests -v
```
