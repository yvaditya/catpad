"""Set the active 3D view's camera: orthographic, or a perspective whose
field of view matches a full-frame photo lens (vertical FOV = 2·atan(12/f),
36×24 mm sensor)."""
import math

import pythoncom

from ..connection import connect

OPTIONS = [
    {"key": "ortho", "label": "Orthographic", "hint": "parallel, no FOV"},
    {"key": "50", "label": "50 mm equivalent", "hint": "27° — natural"},
    {"key": "35", "label": "35 mm equivalent", "hint": "38° — gentle wide"},
    {"key": "24", "label": "24 mm equivalent", "hint": "53° — wide"},
    {"key": "16", "label": "16 mm equivalent", "hint": "74° — ultra-wide"},
]

PARALLEL, PERSPECTIVE = 0, 1  # catProjectionCylindric / catProjectionConic


def run(log, option="ortho"):
    """Entry point called by the pad. Returns a summary string."""
    pythoncom.CoInitialize()
    try:
        catia = connect()
        try:
            viewer = catia.ActiveWindow.ActiveViewer
            viewpoint = viewer.Viewpoint3D
        except Exception:
            return "No active 3D view found — open a model first."

        if option == "ortho":
            try:
                viewpoint.ProjectionMode = PARALLEL
            except Exception:
                return "This view refused the projection change."
            msg = "Orthographic — parallel projection, no lens distortion."
        else:
            focal = float(option)
            half_fov = math.degrees(math.atan(12.0 / focal))
            try:
                viewpoint.ProjectionMode = PERSPECTIVE
                viewpoint.FieldOfView = half_fov
            except Exception:
                return "This view refused the perspective/FOV change."
            msg = (f"{option} mm lens — perspective, "
                   f"~{2 * half_fov:.0f}° vertical field of view.")
        try:
            viewer.Update()
        except Exception:
            pass
        return msg
    finally:
        pythoncom.CoUninitialize()
