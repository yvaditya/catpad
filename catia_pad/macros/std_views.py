"""Snap the active 3D view to a standard orientation, or look normal to
the selected planar face.

All fixed views (isometric included) set the Viewpoint3D sight/up
vectors directly (CATIA convention: front looks along +Y with Z up) and
reframe — StartCommand("Isometric") exists as a command title but
silently no-ops in this editor context (verified live 2026-08-15).
Normal-to measures the selected face's plane via the SPA workbench and
aims the camera down its normal, keeping the current zoom.
"""
import math

import pythoncom

from ..connection import connect
from ..viewpoint import CATSCRIPT, get_triplet, put_triplet

OPTIONS = [
    {"key": "front", "label": "Front", "hint": "XZ · looks +Y"},
    {"key": "back", "label": "Back", "hint": "XZ · looks −Y"},
    {"key": "left", "label": "Left", "hint": "YZ · looks +X"},
    {"key": "right", "label": "Right", "hint": "YZ · looks −X"},
    {"key": "top", "label": "Top", "hint": "XY · looks −Z"},
    {"key": "bottom", "label": "Bottom", "hint": "XY · looks +Z"},
    {"key": "iso", "label": "Isometric", "hint": "corner view, Z up"},
    {"key": "normal", "label": "Normal to Face", "hint": "pick a face first"},
]

# (sight, up) per view; iso looks from (1,1,1) toward the origin with
# the up vector = +Z projected square to that sight line
_ISO = 3 ** -0.5
VIEWS = {
    "front": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "back": ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    "left": ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "right": ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "top": ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    "bottom": ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    "iso": ((-_ISO, -_ISO, -_ISO),
            (-(6 ** -0.5), -(6 ** -0.5), 2 * 6 ** -0.5)),
}


def _unit(v):
    norm = math.sqrt(sum(c * c for c in v))
    if norm < 1e-12:
        raise ValueError("zero-length vector")
    return [c / norm for c in v]


# GetPlane has the same [in]-only CATSafeArrayVariant problem as the
# viewpoint getters, so the whole measure runs in-process via Evaluate.
_PLANE_SCRIPT = """Function GetFacePlane()
    Dim c(8)
    Dim sel
    Set sel = CATIA.ActiveEditor.Selection
    Set meas = CATIA.ActiveDocument.GetWorkbench("SPAWorkbench") _
        .GetMeasurable(sel.Item2(1).Reference)
    meas.GetPlane c
    GetFacePlane = c
End Function"""


def _face_plane(catia):
    """Origin + two in-plane axes of the selected planar face, via the
    SPA (measure) workbench."""
    v = [float(c) for c in catia.SystemService.Evaluate(
        _PLANE_SCRIPT, CATSCRIPT, "GetFacePlane", [])]
    return v[0:3], v[3:6], v[6:9]


def _aim_normal(catia, viewer, viewpoint):
    sel = catia.ActiveEditor.Selection
    try:
        count = sel.Count2
    except Exception:
        count = sel.Count
    if count < 1:
        return "Select a planar face first, then tap Normal to Face."
    try:
        _, a1, a2 = _face_plane(catia)
    except Exception:
        return ("Couldn't measure that selection — pick a planar face "
                "(curved faces have no single normal).")
    normal = _unit([a1[1] * a2[2] - a1[2] * a2[1],
                    a1[2] * a2[0] - a1[0] * a2[2],
                    a1[0] * a2[1] - a1[1] * a2[0]])
    old_sight = _unit(get_triplet(catia, "GetSightDirection"))
    # look at the face from the side we were already on
    if sum(n * s for n, s in zip(normal, old_sight)) < 0:
        normal = [-c for c in normal]
    old_up = get_triplet(catia, "GetUpDirection")
    dot = sum(u * n for u, n in zip(old_up, normal))
    up = [u - dot * n for u, n in zip(old_up, normal)]
    try:
        up = _unit(up)
    except ValueError:  # old up was parallel to the new sight line
        up = [0.0, 0.0, 1.0] if abs(normal[2]) < 0.9 else [0.0, 1.0, 0.0]
    put_triplet(viewpoint, "PutSightDirection", normal)
    put_triplet(viewpoint, "PutUpDirection", up)
    return "Looking square onto the selected face — zoom kept."


def run(log, option="iso"):
    """Entry point called by the pad. Returns a summary string."""
    pythoncom.CoInitialize()
    try:
        catia = connect()
        try:
            viewer = catia.ActiveWindow.ActiveViewer
            viewpoint = viewer.Viewpoint3D
        except Exception:
            return "No active 3D view found — open a model first."

        if option == "normal":
            msg = _aim_normal(catia, viewer, viewpoint)
        elif option in VIEWS:
            sight, up = VIEWS[option]
            try:
                put_triplet(viewpoint, "PutSightDirection", sight)
                put_triplet(viewpoint, "PutUpDirection", up)
                viewer.Reframe()
            except Exception:
                return "This view refused the camera change."
            name = "Isometric" if option == "iso" else option.capitalize()
            msg = f"{name} view, reframed."
        else:
            return f"Unknown view: {option!r}"

        try:
            viewer.Update()
        except Exception:
            pass
        return msg
    finally:
        pythoncom.CoUninitialize()
