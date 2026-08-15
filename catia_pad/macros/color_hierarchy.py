"""Color everything under the selected tree node(s), hierarchically.

Scope is whatever the user selected in the CATIA tree (falls back to the
whole active model when nothing is selected). Top-level items get clearly
different muted hues; each level deeper the sibling hues get closer, and
bodies inside one geoset differ mainly by saturation/lightness.
"""
import pythoncom

from .. import palette
from ..connection import (connect, get_active_root, get_selection,
                          is_hidden, set_color, set_refresh)
from ..tree import (ensure_loaded as _ensure_loaded,
                    loaded_children as _loaded_children,
                    selected_roots as _selected_roots)

MAX_DEPTH = 8


def _paint_level(sel, kids, hue_center, window, depth, stats):
    n = len(kids)
    leaf_i = 0
    for i, (obj, is_leaf) in enumerate(kids):
        if is_hidden(sel, obj):
            stats["skipped"] += 1
            continue
        hue = palette.sibling_hue(hue_center, i, n, window)
        sub = None if is_leaf else _loaded_children(obj, stats)
        if sub and depth < MAX_DEPTH:
            _paint_level(sel, sub, hue, window * palette.SHRINK, depth + 1, stats)
        else:
            # containers we can't see inside get painted whole — one color
            # per component is still the right look
            if set_color(sel, obj, palette.leaf_rgb(hue, leaf_i)):
                stats["colored"] += 1
            else:
                stats["skipped"] += 1
            leaf_i += 1


def run(log):
    """Entry point called by the pad. Returns a summary string."""
    pythoncom.CoInitialize()
    try:
        catia = connect()
        try:
            sel = get_selection(catia)
        except Exception:
            return "Nothing is open in CATIA — open a model first."

        roots = _selected_roots(sel)
        scope = f"{len(roots)} selected item(s)" if roots else "active model"
        if not roots:
            root = get_active_root(catia)
            if root is None:
                return "No selection and no active model found."
            roots = [root]
        stats = {"colored": 0, "skipped": 0, "loaded": 0}

        log(f"Loading unloaded components under {scope}…")
        for root in roots:
            _ensure_loaded(root)

        log(f"Coloring under {scope}…")
        top = []
        for root in roots:
            kids = _loaded_children(root, stats)
            top += kids if kids else [(root, True)]
        if not top:
            return "Found nothing colorable under the selection."

        set_refresh(catia, False)
        try:
            leaf_i = 0
            for i, (obj, is_leaf) in enumerate(top):
                if is_hidden(sel, obj):
                    stats["skipped"] += 1
                    continue
                hue = palette.top_hue(i)
                sub = None if is_leaf else _loaded_children(obj, stats)
                if sub:
                    _paint_level(sel, sub, hue, palette.TOP_WINDOW, 1, stats)
                else:
                    if set_color(sel, obj, palette.leaf_rgb(hue, leaf_i)):
                        stats["colored"] += 1
                    else:
                        stats["skipped"] += 1
                    leaf_i += 1
        finally:
            set_refresh(catia, True)

        msg = f"Colored {stats['colored']} item(s) under {scope}."
        if stats["loaded"]:
            msg += f" Loaded {stats['loaded']} component(s) on the fly."
        if stats["skipped"]:
            msg += f" Skipped {stats['skipped']} (hidden or not colorable)."
        return msg
    finally:
        pythoncom.CoUninitialize()
