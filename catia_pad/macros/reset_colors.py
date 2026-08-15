"""Give every visible item its inherited color back.

Walks the whole active model — products, parts, bodies, geosets, shapes —
and drops the color override on each visible node (SetRealColor with the
inheritance flag 0), undoing whatever the color cards (or anyone else)
painted. Hidden items and everything under a hidden container are left
alone: the card only touches the visible space.
"""
import pythoncom

from ..connection import (connect, get_active_root, get_selection,
                          is_hidden, set_color, set_refresh)
from ..tree import loaded_children

MAX_DEPTH = 8


def _reset(sel, node, depth, stats):
    if is_hidden(sel, node):
        stats["skipped"] += 1
        return
    if set_color(sel, node, None):
        stats["reset"] += 1
    if depth >= MAX_DEPTH:
        return
    for obj, is_leaf in loaded_children(node, stats):
        if not is_leaf:
            _reset(sel, obj, depth + 1, stats)
        elif is_hidden(sel, obj):
            stats["skipped"] += 1
        elif set_color(sel, obj, None):
            stats["reset"] += 1


def run(log):
    """Entry point called by the pad. Returns a summary string."""
    pythoncom.CoInitialize()
    try:
        catia = connect()
        try:
            sel = get_selection(catia)
        except Exception:
            return "Nothing is open in CATIA — open a model first."
        root = get_active_root(catia)
        if root is None:
            return "No active model found."

        stats = {"reset": 0, "skipped": 0, "loaded": 0}
        log("Resetting colors in the visible space…")
        set_refresh(catia, False)
        try:
            _reset(sel, root, 0, stats)
        finally:
            set_refresh(catia, True)

        msg = f"Reset colors on {stats['reset']} item(s)."
        if stats["skipped"]:
            msg += f" Left {stats['skipped']} hidden item(s) untouched."
        return msg
    finally:
        pythoncom.CoUninitialize()
