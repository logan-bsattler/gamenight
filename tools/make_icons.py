#!/usr/bin/env python3
"""Generate the app icons and the link-preview image.

The glyph is the same die that sits in the header's random-pick button, so the
home screen icon and the app agree. Geometry is copied from that SVG's 24-unit
viewBox (rect 3,3 18x18 rx4; pips r1.3 at 8.5, 12, 15.5 on the diagonal) and
scaled up, rather than redrawn by eye.

    python tools/make_icons.py

Needs Pillow. Rerun after changing the palette in index.html.
"""
import os
from PIL import Image, ImageDraw, ImageFont

BG   = (14, 17, 22)      # --bg, the dark chrome
ACC  = (94, 234, 212)    # --acc
DIM  = (147, 161, 179)   # --dim
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "C:/Windows/Fonts/segoeuib.ttf"


def die(size, glyph_frac=0.73):
    """Icon at `size` px: full-bleed background, die centred.

    glyph_frac keeps the die inside the centre 80% circle that Android's
    maskable crop preserves, so one file serves "any maskable".
    """
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)
    span = size * glyph_frac          # the 24-unit viewBox maps to this
    u = span / 24.0                   # px per viewBox unit
    off = (size - span) / 2.0
    p = lambda v: off + v * u

    d.rounded_rectangle([p(3), p(3), p(21), p(21)],
                        radius=4 * u, outline=ACC, width=int(round(2 * u)))
    for c in (8.5, 12, 15.5):         # three pips down the diagonal
        r = 1.3 * u
        d.ellipse([p(c) - r, p(c) - r, p(c) + r, p(c) + r], fill=ACC)
    return img


def og(w=1200, h=630):
    """Link preview: die and wordmark, centred as one block."""
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    title = ImageFont.truetype(FONT, 96)
    sub = ImageFont.truetype(FONT, 36)

    g, gap, lead = 300, 76, 30
    tw = max(d.textlength("Game Night", font=title),
             d.textlength("what fits tonight", font=sub))
    x0 = (w - (g + gap + tw)) / 2
    img.paste(die(g, glyph_frac=1.0), (int(x0), (h - g) // 2))

    # Stack the two lines on their ink boxes, not the em box, so the pair sits
    # optically centred against the die rather than a few px high.
    tb, sb = title.getbbox("Game Night"), sub.getbbox("what fits tonight")
    th, sh = tb[3] - tb[1], sb[3] - sb[1]
    tx, top = x0 + g + gap, (h - (th + lead + sh)) / 2
    d.text((tx, top - tb[1]), "Game Night", font=title, fill=(232, 237, 244))
    d.text((tx, top + th + lead - sb[1]), "what fits tonight", font=sub, fill=DIM)
    return img


if __name__ == "__main__":
    out = lambda n: os.path.join(HERE, n)
    for px in (192, 512):
        die(px).save(out("icon-%d.png" % px))
    die(180).save(out("apple-touch-icon.png"))     # iOS applies its own mask
    og().save(out("og.png"))
    print("wrote icon-192.png icon-512.png apple-touch-icon.png og.png")
