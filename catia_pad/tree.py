"""Shared helpers for walking CATIA spec trees over COM."""

DESIGN_MODE = 1  # CatWorkModeType.DESIGN_MODE — fully loads component geometry


def items(node, collection):
    """Items of a named COM collection, or [] when the node lacks it."""
    try:
        coll = getattr(node, collection)
        return [coll.Item(i) for i in range(1, coll.Count + 1)]
    except Exception:
        return []


def part_of(product):
    """The Part behind a product node, when reachable."""
    getters = (
        lambda p: p.ReferenceProduct.Parent.Part,
        lambda p: p.Parent.Part,
    )
    for get in getters:
        try:
            part = get(product)
            if part is not None:
                return part
        except Exception:
            pass
    return None


def ensure_loaded(node):
    """Ask CATIA to fully load a lightweight/visualization-mode component."""
    try:
        node.ApplyWorkMode(DESIGN_MODE)
        return True
    except Exception:
        return False


def selected_roots(sel):
    """Objects currently selected in the tree, oldest API first."""
    for count_attr, item_attr in (("Count2", "Item2"), ("Count", "Item")):
        try:
            get = getattr(sel, item_attr)
            return [get(i).Value for i in range(1, getattr(sel, count_attr) + 1)]
        except Exception:
            continue
    return []


def type_name(obj):
    """COM type name of an automation object (e.g. HybridShapePointCoord)."""
    try:
        return obj._oleobj_.GetTypeInfo().GetDocumentation(-1)[0]
    except Exception:
        return ""
