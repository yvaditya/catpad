"""One flat, clearly different color per body/geoset, for every visible
part in the model.

Unlike Color by Hierarchy this never descends inside a geoset and ignores
the tree structure when picking colors: every body and top-level geoset
across the whole model gets its own well-spread muted hue (applied with
inheritance, so everything inside follows), so neighboring bodies never
share a family.
"""
import pythoncom

from .. import palette
from ..connection import (connect, get_active_root, get_selection,
                          is_hidden, set_color, set_refresh)
from ..tree import ensure_loaded, items, part_of, ref_name, sub_products


def _parts(node, found, stats):
    """Collect leaf products (the parts) under node, loading lightweight
    components on the way down."""
    subs = sub_products(node)
    if not subs and ensure_loaded(node):
        stats["loaded"] += 1
        subs = sub_products(node)
    if subs:
        for sub in subs:
            _parts(sub, found, stats)
    else:
        found.append(node)


def _units(node):
    """Bodies and top-level geosets of one part-level node, loading the
    component first when it looks empty because it isn't loaded."""
    units = _try_units(node)
    if not units and ensure_loaded(node):
        units = _try_units(node)
    return units


def _try_units(node):
    bodies = items(node, "Bodies")
    geosets = items(node, "HybridBodies")
    if not bodies and not geosets:
        part = part_of(node)
        if part is not None:
            bodies = items(part, "Bodies")
            geosets = items(part, "HybridBodies")
    return bodies + geosets


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

        stats = {"loaded": 0}
        log("Finding visible parts…")
        parts = []
        _parts(root, parts, stats)
        if not parts:
            return "Found no parts in the active model."

        log(f"Coloring bodies/geosets across {len(parts)} part(s)…")
        colored = hidden_parts = repeats = 0
        part_i = 0
        # one global sequence: hue walks the curated wheel (then golden-angle
        # steps) while the tone cycles too, so every body lands far from the
        # previous ones in hue AND in saturation/lightness
        k = 0
        seen = set()  # instances of one part share its reference colors
        set_refresh(catia, False)
        try:
            for node in parts:
                if is_hidden(sel, node):
                    hidden_parts += 1
                    continue
                key = ref_name(node)
                if key in seen:
                    repeats += 1
                    continue
                seen.add(key)
                part_i += 1
                units = _units(node) or [node]  # nothing inside -> paint whole
                for unit in units:
                    if is_hidden(sel, unit):
                        continue
                    if set_color(sel, unit,
                                 palette.leaf_rgb(palette.top_hue(k), k)):
                        colored += 1
                        k += 1
        finally:
            set_refresh(catia, True)

        msg = f"Colored {colored} body/geoset(s) across {part_i} visible part(s)."
        if repeats:
            msg += f" {repeats} repeated instance(s) share their part's colors."
        if hidden_parts:
            msg += f" Skipped {hidden_parts} hidden part(s)."
        if stats["loaded"]:
            msg += f" Loaded {stats['loaded']} component(s) on the fly."
        return msg
    finally:
        pythoncom.CoUninitialize()
