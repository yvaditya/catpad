"""Flip the 3D view's per-element-type display filters — the Points /
Planes / Axis-systems / Wireframe options that live under the View Modes
chooser — without touching the model's hide/show state.

Automation exposes no dedicated API for these filters, so the pad fires
the same UI command the panel option does (CATIA.StartCommand). Command
naming varies between releases: each kind tries the spellings below in
order and the status line reports the first one the session accepted.
If none land, type c: in the Power Input box to list the real command
name, then put it first in _COMMANDS here.
"""
import pythoncom

from ..connection import connect

# What the pad renders: one segment per kind, in this order.
TOGGLES = [
    {"key": "lines", "icon": "line", "label": "Lines",
     "tip": "View filter: display of wireframe lines and curves."},
    {"key": "planes", "icon": "plane", "label": "Planes",
     "tip": "View filter: display of reference planes."},
    {"key": "axes", "icon": "axis", "label": "Axes",
     "tip": "View filter: display of axis systems."},
    {"key": "points", "icon": "point", "label": "Points",
     "tip": "View filter: display of points."},
]

# Candidate StartCommand spellings per kind, most likely first.
_COMMANDS = {
    "lines": ("3D Wireframe", "Wireframe", "Lines and Curves", "Lines"),
    "planes": ("Planes", "Plane"),
    "axes": ("Axis Systems", "Axis System", "Axes"),
    "points": ("Points", "Point"),
}

_LABELS = {"lines": "Lines", "planes": "Planes",
           "axes": "Axis systems", "points": "Points"}


def run(log, option=None):
    """Entry point called by the pad. option is "<kind>:<show|hide>";
    the direction is the pad's own bookkeeping — the underlying UI
    command is a pure toggle."""
    kind = (option or "").partition(":")[0]
    commands = _COMMANDS.get(kind)
    if commands is None:
        return f"Unknown visibility toggle: {option!r}"
    label = _LABELS[kind]

    pythoncom.CoInitialize()
    try:
        catia = connect()
        for cmd in commands:
            log(f"Toggling {label} filter ('{cmd}')…")
            try:
                catia.StartCommand(cmd)
            except Exception:
                continue
            return f"{label} view filter toggled (command '{cmd}')."
        return (f"The session accepted no {label} filter command — find "
                "its name with the c: Power Input box, then add it to "
                "_COMMANDS in toggle_visibility.py.")
    finally:
        pythoncom.CoUninitialize()
