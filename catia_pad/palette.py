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
    (0.34, 0.66),
    (0.42, 0.58),
    (0.26, 0.72),
    (0.38, 0.62),
    (0.30, 0.54),
    (0.46, 0.68),
]

# Every final color is blended slightly toward this warm gray so the whole
# palette reads as one coordinated family instead of independent colors.
HARMONY_GRAY = (184, 178, 168)
HARMONY = 0.12


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


def _tune(hue, sat, light):
    """Per-hue correction — HLS treats all hues alike, eyes don't."""
    h = hue % 360.0
    if 40 <= h < 95:  # yellows/olives go mustard when dark or saturated
        sat *= 0.72
        light += 0.05
    elif 95 <= h < 165:  # greens get garish fast
        sat *= 0.85
    elif h < 40 or h >= 330:  # reds/oranges feel heavy
        sat *= 0.88
        light += 0.03
    elif 270 <= h < 330:  # magentas/pinks turn candy
        sat *= 0.82
    return sat, min(max(light, 0.52), 0.74)


def leaf_rgb(hue, leaf_index):
    """Final muted RGB for a colorable leaf, varying tone by sibling index."""
    sat, light = LEAF_TONES[leaf_index % len(LEAF_TONES)]
    sat, light = _tune(hue, sat, light)
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, light, sat)
    return tuple(
        round(c * 255 * (1 - HARMONY) + g_ * HARMONY)
        for c, g_ in zip((r, g, b), HARMONY_GRAY)
    )
