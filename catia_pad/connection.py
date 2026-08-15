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


SHOWN, HIDDEN = 0, 1  # CatVisPropertyShow attribute values


def show_state(vis_properties):
    """Show attribute of the current selection (SHOWN or HIDDEN).

    This 3DX build returns GetShow as a (flags, state) tuple — the state
    sits last (verified live: hidden items give (0, 1), shown give (0, 0)).
    Plain ints are passed through for other builds.
    """
    raw = vis_properties.GetShow()
    if isinstance(raw, tuple):
        raw = raw[-1]
    return raw


def is_hidden(sel, obj):
    """True when the object itself is flagged hidden. Containers gate
    their whole subtree: a hidden geoset means nothing inside it shows,
    whatever the children's own flags say."""
    try:
        sel.Clear()
        sel.Add(obj)
        return show_state(sel.VisProperties) == HIDDEN
    except Exception:
        return False  # can't query -> treat as visible


def set_color(sel, obj, rgb):
    """Color one object (with inheritance), or hand the color back to the
    parent when rgb is None — SetRealColor's inheritance flag 0 drops the
    override so the item inherits again."""
    try:
        sel.Clear()
        sel.Add(obj)
        vis = sel.VisProperties
    except Exception:
        return False
    try:
        if rgb is None:
            vis.SetRealColor(0, 0, 0, 0)
        else:
            r, g, b = rgb
            vis.SetRealColor(int(r), int(g), int(b), 1)
        return True
    except Exception:
        return False
    finally:
        try:
            sel.Clear()
        except Exception:
            pass


def set_refresh(catia, on):
    """Toggle display refresh; ignored on sessions that don't expose it."""
    try:
        catia.RefreshDisplay = on
    except Exception:
        pass
