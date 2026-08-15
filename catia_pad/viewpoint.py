"""Viewpoint3D access that survives out-of-process COM.

Two hard-won B428 facts (probed live 2026-08-15):

- Put*Direction / PutOrigin accept a plain Python list. Wrapping the
  vector in win32com VARIANT(VT_ARRAY | VT_R8[, | VT_BYREF]) raises a
  client-side TypeError before any COM call happens — that error, caught
  and reworded, was the old "view refused the camera change".
- Get* methods declare their CATSafeArrayVariant parameter [in]-only, so
  the filled values never marshal back to an external process: the call
  "succeeds" and hands back the zeros you sent. The working route is
  SystemService.Evaluate running a tiny CATScript in-process and
  returning the array as the function result.
"""

CATSCRIPT = 0  # SystemService.Evaluate language id, verified live

_GET3 = """Function Get3()
    Dim v(2)
    CATIA.ActiveWindow.ActiveViewer.Viewpoint3D.{name} v
    Get3 = v
End Function"""


def get_triplet(catia, name):
    """[x, y, z] from a Viewpoint3D getter (GetSightDirection, GetOrigin,
    GetUpDirection, …) of the active viewer."""
    res = catia.SystemService.Evaluate(
        _GET3.format(name=name), CATSCRIPT, "Get3", [])
    return [float(c) for c in res]


def put_triplet(viewpoint, name, vec):
    """Send [x, y, z] to a Viewpoint3D setter (PutSightDirection, …)."""
    getattr(viewpoint, name)([float(c) for c in vec])
