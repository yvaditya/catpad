# CATIA 3DX Macro Pad

A small always-on-top control pad that sits outside CATIA 3DEXPERIENCE and
drives the running session over COM. Click a button on the pad, the macro
runs on whatever you have selected in the CATIA tree.

## Macros

### Color by Hierarchy

Select any node in the tree (assembly, part, geoset — or nothing to target
the whole active model) and hit the button. Everything under it gets a
muted, easy-on-the-eyes color, assigned **logically by tree structure**:

- Top-level items get clearly different hues (sage, dusty blue,
  terracotta, slate teal, …).
- One level down, siblings stay near the parent's hue, slightly shifted.
- Bodies inside the same geoset share one hue family and differ mainly by
  saturation/lightness.

Hidden items are skipped. Components the macro can't open up are painted
whole with one color.

## Setup

Needs Python 3.11+ on Windows and a running 3DEXPERIENCE native client.

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Run

Double-click `run_pad.bat`, or from a terminal (shows errors, useful for
debugging):

```powershell
.venv\Scripts\python macro_pad.py
```

## Adding a macro

1. Add a module under `catia_pad/macros/` exposing `run(log) -> str`.
2. Append `("Button label", your_module.run)` to `MACROS` in
   `macro_pad.py`. The grid lays itself out.

## Layout

```
macro_pad.py              entry point / tkinter pad UI
catia_pad/connection.py   attach to the running session (pywin32)
catia_pad/palette.py      hierarchical muted color math
catia_pad/macros/         one module per button
tests/test_palette.py     palette sanity checks (no CATIA needed)
```
