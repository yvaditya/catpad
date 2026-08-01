"""Color everything under the selected tree node(s), hierarchically.

Scope is whatever the user selected in the CATIA tree (falls back to the
whole active model when nothing is selected). Top-level items get clearly
different muted hues; each level deeper the sibling hues get closer, and
bodies inside one geoset differ mainly by saturation/lightness.
"""
import pythoncom

from .. import palette
from ..connection import connect, get_selection, get_active_root, set_refresh
from ..tree import (items as _items, part_of as _part_of,
                    ensure_loaded as _ensure_loaded,
                    selected_roots as _selected_roots)

MAX_DEPTH = 8

HIDDEN = 1  # catVisPropertyNoShowAttr


def _enumerate(node):
    """Children as (object, is_leaf) pairs.

    Sub-products and geosets recurse; bodies and individual shapes are
    leaves (coloring a body with inheritance covers everything inside it).
    """
    kids = [(p, False) for p in _items(node, "Products")]
    bodies = _items(node, "Bodies")
    geosets = _items(node, "HybridBodies")
    if not kids and not bodies and not geosets:
        part = _part_of(node)
        if part is not None:
            bodies = _items(part, "Bodies")
            geosets = _items(part, "HybridBodies")
    kids += [(b, True) for b in bodies]
    kids += [(g, False) for g in geosets]
    kids += [(s, True) for s in _items(node, "HybridShapes")]
    return kids


def _tagged_children(node, stats=None):
    """Enumerate children; if a component looks empty because it isn't
    loaded, load it and enumerate again."""
    kids = _enumerate(node)
    if not kids and _ensure_loaded(node):
        if stats is not None:
            stats["loaded"] += 1
        kids = _enumerate(node)
    return kids


def _apply_color(sel, obj, rgb):
    """Color one object (with inheritance) unless it is hidden."""
    try:
        sel.Clear()
        sel.Add(obj)
        vis = sel.VisProperties
    except Exception:
        return False
    try:
        if vis.GetShow() == HIDDEN:
            return False
    except Exception:
        pass  # can't query visibility on this session -> color it anyway
    try:
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


def _paint_level(sel, kids, hue_center, window, depth, stats):
    n = len(kids)
    leaf_i = 0
    for i, (obj, is_leaf) in enumerate(kids):
        hue = palette.sibling_hue(hue_center, i, n, window)
        sub = None if is_leaf else _tagged_children(obj, stats)
        if sub and depth < MAX_DEPTH:
            _paint_level(sel, sub, hue, window * palette.SHRINK, depth + 1, stats)
        else:
            # containers we can't see inside get painted whole — one color
            # per component is still the right look
            if _apply_color(sel, obj, palette.leaf_rgb(hue, leaf_i)):
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
            kids = _tagged_children(root, stats)
            top += kids if kids else [(root, True)]
        if not top:
            return "Found nothing colorable under the selection."

        set_refresh(catia, False)
        try:
            leaf_i = 0
            for i, (obj, is_leaf) in enumerate(top):
                hue = palette.top_hue(i)
                sub = None if is_leaf else _tagged_children(obj, stats)
                if sub:
                    _paint_level(sel, sub, hue, palette.TOP_WINDOW, 1, stats)
                else:
                    if _apply_color(sel, obj, palette.leaf_rgb(hue, leaf_i)):
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
