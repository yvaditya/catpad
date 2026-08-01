# CatPad — CATIA 3DX Macro Pad

by Aditya Yerra

A small always-on-top control pad that sits outside CATIA 3DEXPERIENCE and
drives the running session over COM. Click a card on the pad, the macro
runs on whatever you have selected in the CATIA tree.

The pad is a frameless macOS-style panel (pywebview + WebView2): drag it
by its top bar, yellow dot minimizes, red dot closes, hover a card for a
tooltip.

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

Hidden items are skipped. Components opened lightweight (visualization
mode) are switched to fully loaded (design mode) first, then colored.
Components the macro still can't open up are painted whole with one color.

### Camera Lens

Tap the card, pick a lens in the popup sheet: **Orthographic** (parallel
projection) or a **50 / 35 / 24 / 16 mm** full-frame equivalent. The
active 3D view switches projection and field of view to match
(vertical FOV = 2·atan(12/focal)).

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

## Standalone app

`build_app.bat` packages everything into a single `dist\CatPad.exe`
(PyInstaller) that runs on any Windows 11 machine without Python — only
Microsoft's WebView2 runtime is needed, which ships with Windows 11.

## Adding a macro

The pad shows 8 slots; unused ones appear as dimmed `+` placeholders
waiting for future macros.

1. Add a module under `catia_pad/macros/` exposing `run(log) -> str`.
2. Append an entry (key, icon, label, tip, fn) to `MACROS` in
   `macro_pad.py` — it fills the next free slot (the grid grows past 8
   automatically if needed). New icon? Add an SVG to `ICONS` in
   `ui/index.html`.

## Layout

```
macro_pad.py              entry point / pywebview shell + JS bridge
ui/index.html             the pad UI (HTML/CSS/JS, macOS styling)
catia_pad/connection.py   attach to the running session (pywin32)
catia_pad/palette.py      hierarchical muted color math
catia_pad/macros/         one module per button
tests/test_palette.py     palette sanity checks (no CATIA needed)
```
