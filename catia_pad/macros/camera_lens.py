"""Set the active 3D view's camera: orthographic, or a perspective whose
field of view matches a full-frame photo lens (vertical FOV = 2·atan(12/f),
36×24 mm sensor)."""
import math

import pythoncom

from ..connection import connect
from ..viewpoint import get_triplet, put_triplet

OPTIONS = [
    {"key": "ortho", "label": "Orthographic", "hint": "parallel, no FOV"},
    {"key": "50", "label": "50 mm", "hint": "27° — natural"},
    {"key": "35", "label": "35 mm", "hint": "38° — gentle wide"},
    {"key": "24", "label": "24 mm", "hint": "53° — wide"},
    {"key": "16", "label": "16 mm", "hint": "74° — ultra-wide"},
]

# CatProjectionMode: conic (perspective) = 0, cylindric (parallel) = 1 —
# confirmed live: sending 0 produced perspective, 1 produced parallel.
PERSPECTIVE, PARALLEL = 0, 1


def _keep_subject_size(catia, viewpoint, half_new_deg):
    """Dolly the camera along its sight line so the model keeps its
    apparent size while the lens (FOV) changes — only meaningful when the
    view is already perspective."""
    half_old = math.radians(viewpoint.FieldOfView)
    half_new = math.radians(half_new_deg)
    if half_old <= 0 or abs(half_old - half_new) < 1e-9:
        return False
    origin = get_triplet(catia, "GetOrigin")
    sight = get_triplet(catia, "GetSightDirection")
    norm = math.sqrt(sum(c * c for c in sight))
    if norm < 1e-12:
        return False
    sight = [c / norm for c in sight]
    d_old = viewpoint.FocusDistance
    if d_old <= 0:
        return False
    target = [o + s * d_old for o, s in zip(origin, sight)]
    d_new = d_old * math.tan(half_old) / math.tan(half_new)
    new_origin = [t - s * d_new for t, s in zip(target, sight)]
    put_triplet(viewpoint, "PutOrigin", new_origin)
    viewpoint.FocusDistance = d_new
    return True


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
            dollied = False
            try:
                if viewpoint.ProjectionMode == PERSPECTIVE:
                    dollied = _keep_subject_size(catia, viewpoint, half_fov)
            except Exception:
                dollied = False
            try:
                viewpoint.ProjectionMode = PERSPECTIVE
                viewpoint.FieldOfView = half_fov
            except Exception:
                return "This view refused the perspective/FOV change."
            msg = (f"{option} mm lens — perspective, "
                   f"~{2 * half_fov:.0f}° vertical field of view.")
            if dollied:
                msg += " Camera dollied to keep the model the same size."
        try:
            viewer.Update()
        except Exception:
            pass
        return msg
    finally:
        pythoncom.CoUninitialize()
