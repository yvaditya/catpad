"""Muted color generation that mirrors the model tree.

Hue distance encodes tree distance: top-level siblings get clearly
different hues, each level deeper the sibling hue window shrinks, and
leaves inside one container (e.g. bodies in a geoset) share a hue family
and differ mainly by saturation/lightness.
"""
import colorsys

# Curated muted anchor hues (degrees) for top-level items, ordered so
# consecutive entries sit far apart on the wheel:
# sage, dusty blue, terracotta, slate teal, sand, mauve,
# olive, periwinkle, dusty rose, seafoam, clay, plum.
BASE_HUES = [95.0, 215.0, 18.0, 183.0, 40.0, 310.0,
             65.0, 240.0, 0.0, 155.0, 28.0, 285.0]

GOLDEN_ANGLE = 137.508

# Total hue spread among siblings one level below a top-level item;
# each level deeper multiplies the window by SHRINK.
TOP_WINDOW = 44.0
SHRINK = 0.4

# Leaf siblings cycle through these (saturation, lightness) pairs so bodies
# in the same geoset read as one family separated by tone, not hue.
# All pairs stay in the muted band: no neon, no mud.
LEAF_TONES = [
    (0.30, 0.60),
    (0.42, 0.52),
    (0.24, 0.68),
    (0.38, 0.57),
    (0.28, 0.50),
    (0.45, 0.64),
]


def top_hue(index):
    """Hue for the index-th top-level item, extending past the curated
    list with golden-angle steps so any count stays well spread."""
    if index < len(BASE_HUES):
        return BASE_HUES[index]
    return (BASE_HUES[-1] + (index - len(BASE_HUES) + 1) * GOLDEN_ANGLE) % 360.0


def sibling_hue(center, index, count, window):
    """Spread `count` sibling hues across `window` degrees centered on the
    parent's hue."""
    if count <= 1:
        return center % 360.0
    return (center + window * (index / (count - 1) - 0.5)) % 360.0


def leaf_rgb(hue, leaf_index):
    """Final muted RGB for a colorable leaf, varying tone by sibling index."""
    sat, light = LEAF_TONES[leaf_index % len(LEAF_TONES)]
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, light, sat)
    return round(r * 255), round(g * 255), round(b * 255)
