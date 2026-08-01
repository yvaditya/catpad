"""Attach to the running 3DEXPERIENCE / CATIA session over COM."""
import pythoncom
import win32com.client

PROG_IDS = ("CATIA.Application", "3DEXPERIENCE.Application")


class CatiaNotRunning(RuntimeError):
    pass


def connect():
    for prog_id in PROG_IDS:
        try:
            return win32com.client.GetObject(Class=prog_id)
        except pythoncom.com_error:
            continue
    raise CatiaNotRunning(
        "No running 3DEXPERIENCE session found. Start CATIA and open a model."
    )


def get_selection(catia):
    try:
        return catia.ActiveEditor.Selection  # 3DEXPERIENCE native
    except Exception:
        return catia.ActiveDocument.Selection  # V5-style fallback


def get_active_root(catia):
    """Root object of whatever is open, used when nothing is selected."""
    getters = (
        lambda c: c.ActiveEditor.ActiveObject,
        lambda c: c.ActiveDocument.Product,
        lambda c: c.ActiveDocument.Part,
    )
    for get in getters:
        try:
            obj = get(catia)
            if obj is not None:
                return obj
        except Exception:
            pass
    return None


def set_refresh(catia, on):
    """Toggle display refresh; ignored on sessions that don't expose it."""
    try:
        catia.RefreshDisplay = on
    except Exception:
        pass
