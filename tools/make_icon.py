"""Regenerate assets/catpad.ico — the 🐈 (U+1F408) cat rendered from
Segoe UI Emoji. Dev-only script (needs Pillow); the .ico is committed,
so this only reruns when the logo changes."""
from pathlib import Path

from PIL import Image, ImageFont

CAT = "\U0001F408"
FONT = r"C:\Windows\Fonts\seguiemj.ttf"
SIZES = (256, 64, 48, 32, 24, 16)
OUT = Path(__file__).resolve().parent.parent / "assets" / "catpad.ico"


def render(px):
    # Segoe UI Emoji is a bitmap-strike color font: FreeType only takes
    # the strike sizes, so render at the font's fixed size and rescale.
    font = ImageFont.truetype(FONT, 128)
    img = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    from PIL import ImageDraw
    ImageDraw.Draw(img).text((80, 80), CAT, font=font,
                             embedded_color=True, anchor="mm")
    box = img.getbbox()
    if box:
        img = img.crop(box)
    side = max(img.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    return square.resize((px, px), Image.LANCZOS)


def main():
    OUT.parent.mkdir(exist_ok=True)
    imgs = [render(s) for s in SIZES]
    imgs[0].save(OUT, format="ICO",
                 append_images=imgs[1:],
                 sizes=[(s, s) for s in SIZES])
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
