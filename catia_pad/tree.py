"""Shared helpers for walking CATIA spec trees over COM."""

DESIGN_MODE = 1  # CatWorkModeType.DESIGN_MODE — fully loads component geometry


def items(node, collection):
    """Items of a named COM collection, or [] when the node lacks it."""
    try:
        coll = getattr(node, collection)
        return [coll.Item(i) for i in range(1, coll.Count + 1)]
    except Exception:
        return []


def sub_products(node):
    """Child product nodes: V5-style .Products, or .Occurrences on the
    3DX occurrence tree (what get_active_root actually returns — a
    VPMRootOccurrence whose children are VPMOccurrences)."""
    subs = items(node, "Products")
    return subs if subs else items(node, "Occurrences")


def _rep_part(product):
    """3DX route: the Part lives inside the 3D Shape representation.

    An occurrence-tree node resolves VPMOccurrence -> VPMInstance ->
    VPMReference; the reference's RepInstances point at VPMRepReferences
    (the 3D Shapes) and GetItem("Part") hands over the Part with the
    bodies/geosets (whole chain verified live on B428, 2026-08-15).
    """
    refs = [product]
    for get in (lambda p: p.InstanceOccurrenceOf.ReferenceInstanceOf,
                lambda p: p.ReferenceInstanceOf,
                lambda p: p.ReferenceRootOccurrenceOf,
                lambda p: p.ReferenceProduct):
        try:
            ref = get(product)
            if ref is not None:
                refs.append(ref)
        except Exception:
            pass
    for ref in refs:
        try:
            reps = ref.RepInstances
            count = reps.Count
        except Exception:
            continue
        for i in range(1, count + 1):
            try:
                rep_ref = reps.Item(i).ReferenceInstanceOf
            except Exception:
                continue
            for extract in (lambda r: r.GetItem("Part"),
                            lambda r: r.GetDocument().Part):
                try:
                    part = extract(rep_ref)
                    if part is not None:
                        return part
                except Exception:
                    continue
    return None


def ref_name(node):
    """Name of the reference behind an instance/occurrence node — the
    dedup key when one part is instanced several times."""
    for get in (lambda p: p.InstanceOccurrenceOf.ReferenceInstanceOf.Name,
                lambda p: p.ReferenceInstanceOf.Name,
                lambda p: p.ReferenceProduct.Name):
        try:
            return get(node)
        except Exception:
            continue
    try:
        return node.Name
    except Exception:
        return None


def part_of(product):
    """The Part behind a product node, when reachable."""
    getters = (
        lambda p: p.ReferenceProduct.Parent.Part,
        lambda p: p.Parent.Part,
        _rep_part,
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


def child_nodes(node):
    """Children as (object, is_leaf) pairs.

    Sub-products and geosets recurse; bodies and individual shapes are
    leaves (coloring a body with inheritance covers everything inside it).
    """
    kids = [(p, False) for p in sub_products(node)]
    bodies = items(node, "Bodies")
    geosets = items(node, "HybridBodies")
    if not kids and not bodies and not geosets:
        part = part_of(node)
        if part is not None:
            bodies = items(part, "Bodies")
            geosets = items(part, "HybridBodies")
    kids += [(b, True) for b in bodies]
    kids += [(g, False) for g in geosets]
    kids += [(s, True) for s in items(node, "HybridShapes")]
    return kids


def loaded_children(node, stats=None):
    """child_nodes, loading the component first when it looks empty
    because it isn't loaded."""
    kids = child_nodes(node)
    if not kids and ensure_loaded(node):
        if stats is not None:
            stats["loaded"] += 1
        kids = child_nodes(node)
    return kids


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
