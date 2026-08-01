"""Render palette_preview.html — a fake model tree colored exactly the way
the macro would color it, so palette tweaks can be judged without CATIA."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from catia_pad import palette

# (component name, [group leaf-counts]) — groups simulate geosets, a count
# in the "loose" slot simulates bodies sitting directly under the part
FAKE_TREE = [
    ("Frame", [5, 3]),
    ("Housing", [4]),
    ("Drivetrain", [3, 4, 2]),
    ("Cover", [6]),
    ("Bracket set", [2, 2]),
    ("Piping", [5]),
    ("Electronics tray", [3, 3]),
    ("Fasteners", [4]),
]


def swatch(rgb, label):
    r, g, b = rgb
    return (
        f'<div class="sw" style="background:rgb({r},{g},{b})">'
        f'<span>{label}</span><code>{r},{g},{b}</code></div>'
    )


def main():
    rows = []
    for i, (name, groups) in enumerate(FAKE_TREE):
        top = palette.top_hue(i)
        cells = []
        n_groups = len(groups)
        for gi, leaf_count in enumerate(groups):
            g_hue = palette.sibling_hue(top, gi, n_groups, palette.TOP_WINDOW)
            leaf_window = palette.TOP_WINDOW * palette.SHRINK
            sws = "".join(
                swatch(
                    palette.leaf_rgb(
                        palette.sibling_hue(g_hue, li, leaf_count, leaf_window), li
                    ),
                    f"Body {li + 1}",
                )
                for li in range(leaf_count)
            )
            cells.append(f'<div class="geoset"><em>Geoset {gi + 1}</em>{sws}</div>')
        rows.append(
            f'<section><h2>{name} <small>hue {top:.0f}°</small></h2>'
            f'<div class="row">{"".join(cells)}</div></section>'
        )

    html = f"""<!doctype html><meta charset="utf-8">
<title>Macro Pad palette preview</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background:#2a2d33; color:#e8e4da;
         margin:2rem; }}
  h1 {{ font-weight:600 }} h2 {{ margin:1.2rem 0 .4rem; font-size:1rem }}
  h2 small {{ color:#9aa; font-weight:400 }}
  .row {{ display:flex; flex-wrap:wrap; gap:.6rem }}
  .geoset {{ border:1px solid #4a4e55; border-radius:8px; padding:.5rem;
             display:flex; gap:.35rem; align-items:flex-end }}
  .geoset em {{ writing-mode:vertical-rl; rotate:180deg; color:#9aa;
                font-size:.7rem; font-style:normal }}
  .sw {{ width:74px; height:74px; border-radius:6px; display:flex;
         flex-direction:column; justify-content:flex-end; padding:.3rem;
         color:rgba(0,0,0,.65); font-size:.68rem }}
  .sw code {{ font-size:.6rem; opacity:.7 }}
</style>
<h1>Palette preview — one fake assembly, colored like the macro would</h1>
<p>Each section = one top-level component. Boxes = geosets: same hue family,
bodies split by tone. Tweak <code>catia_pad/palette.py</code>, rerun
<code>tools\\preview_palette.py</code>, refresh this page.</p>
{"".join(rows)}"""

    out = Path(__file__).resolve().parents[1] / "palette_preview.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
