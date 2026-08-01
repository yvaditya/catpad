"""Sanity checks for the hierarchical palette (no CATIA needed)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from catia_pad import palette


def test_top_hues_spread():
    hues = [palette.top_hue(i) for i in range(20)]
    assert all(0 <= h < 360 for h in hues)
    # consecutive top-level hues must be clearly apart
    for a, b in zip(hues[:11], hues[1:12]):
        d = min(abs(a - b), 360 - abs(a - b))
        assert d > 30, f"top hues too close: {a} vs {b}"


def test_sibling_window_shrinks():
    center = 120.0
    lvl1 = [palette.sibling_hue(center, i, 5, palette.TOP_WINDOW) for i in range(5)]
    lvl2 = [palette.sibling_hue(center, i, 5, palette.TOP_WINDOW * palette.SHRINK)
            for i in range(5)]
    spread1 = max(lvl1) - min(lvl1)
    spread2 = max(lvl2) - min(lvl2)
    assert spread2 < spread1, "deeper siblings must sit closer in hue"
    assert spread1 <= palette.TOP_WINDOW + 1e-6


def test_leaf_rgb_muted_and_distinct():
    seen = set()
    for i in range(6):
        rgb = palette.leaf_rgb(210.0, i)
        assert all(0 <= c <= 255 for c in rgb)
        assert max(rgb) - min(rgb) < 140, f"too saturated for muted look: {rgb}"
        assert 60 < sum(rgb) / 3 < 210, f"too dark/bright: {rgb}"
        seen.add(rgb)
    assert len(seen) == 6, "leaf tones must differ within one hue family"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"{len(fns)} tests passed")
