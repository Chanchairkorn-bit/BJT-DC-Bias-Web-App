# AGENTS.md — Coding conventions for this project

## Purpose

Flask web app that computes the BJT voltage-divider DC bias operating
point for ENG29 2121 Lab 03.

## Rules

- Keep engineering math in `dc_bias.py` only. It must not import Flask,
  HTML or any web framework.
- Keep HTTP/form handling in `app.py`. The template must not contain
  physics equations.
- Internal units are SI (V, Ω, A). Convert each resistor's selected
  unit (Ω / kΩ / MΩ) to Ω at the web layer.
- Every new behavior needs a test under `tests/`.
- Invalid input must produce a readable message, never a 500 error.
- Out-of-region results must carry a warning; do not claim accuracy
  outside the forward-active region.
- Do not commit `.venv/`, `.env`, secrets or credentials.

## Commands

```bash
python -m pip install -r requirements.txt
python -m flask --app app run --debug
python -m unittest discover -s tests -v
```
