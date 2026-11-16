#!/usr/bin/env python3
"""The brand's pictures (assets/brand): the square icon - a bento box, S E I in three
compartments on top, T and ON below - the wordmark, a long shelf with the same compartments
side by side, the small form without letters (16 and 32 px), and the change from the box to
the shelf and back (an animated SVG). The box is lacquer black, as on red and black bento
boxes; S is loud red, the other compartments share one lightness and colourfulness (OKLCH),
their hues running like a rainbow. The letters are outlines (paths) of a font, so the pictures
look the same everywhere, with or without that font installed.

    python3 scripts/make_brand_svgs.py [--font PATH] [--out assets/brand]
"""

import argparse
import math
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:  # started as a script: make core importable
    sys.path.insert(0, str(REPO_ROOT))

from core.brand import NAME, file_name  # noqa: E402

WORD = NAME.upper()  # the name as the pictures show it, in capitals
FONT = Path("/usr/share/fonts/truetype/open-sans/OpenSans-Semibold.ttf")  # SIL Open Font License
FRAME = "#16130f"  # the box and the letters: lacquer black, a little warm
LOUD_RED = "#e2402b"  # the S compartment: vermilion, the one loud colour
LIGHTNESS = 0.87  # the other compartments: one lightness ...
CHROMA = 0.075  # ... and one colourfulness, as much as all of them can show on a screen
HUES = (25, 85, 150, 235, 305)  # S E I T ON, a rainbow (S's is not used while it is loud red)

SIZE = 160
WALL = 10  # outer wall and walls between the compartments: 1 px at 16 px
ROW = (SIZE - 3 * WALL) / 2
COL = (SIZE - 4 * WALL) / 3
LETTER_SIZE = 40
CHANGE_SECONDS = 7  # one round of the change: box, shelf, box


def _srgb(lightness, chroma, hue):
    """OKLCH to sRGB channels (0..1, may lie outside when the colour does not fit)."""
    a, b = chroma * math.cos(math.radians(hue)), chroma * math.sin(math.radians(hue))
    l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    linear = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
              -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
              -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    return [12.92 * v if v <= 0.0031308 else 1.055 * math.copysign(abs(v) ** (1 / 2.4), v) - 0.055
            for v in linear]


def max_chroma(lightness, hue):
    """How colourful hue can be at lightness and still fit on a screen (sRGB)."""
    lo, hi = 0.0, 0.4
    for _ in range(40):
        mid = (lo + hi) / 2
        if all(-1e-6 <= v <= 1 + 1e-6 for v in _srgb(lightness, mid, hue)):
            lo = mid
        else:
            hi = mid
    return lo


def oklch_hex(lightness, chroma, hue):
    return "#" + "".join(f"{round(min(1.0, max(0.0, v)) * 255):02x}" for v in _srgb(lightness, chroma, hue))


def oklch_of(colour):
    """(lightness, chroma, hue) of a #rrggbb colour."""
    def linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (linear(int(colour[i:i + 2], 16) / 255) for i in (1, 3, 5))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    lightness = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    b2 = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return lightness, math.hypot(a, b2), math.degrees(math.atan2(b2, a)) % 360


def compartment_colours():
    """S E I T ON: S loud red, the others one lightness and colourfulness in rainbow hues."""
    return [LOUD_RED] + [oklch_hex(LIGHTNESS, CHROMA, hue) for hue in HUES[1:]]


class Letters:
    def __init__(self, font_path: Path):
        self.font = TTFont(str(font_path))
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.cap_height = self.font["OS/2"].sCapHeight

    def _names(self, text):
        return [self.cmap[ord(c)] for c in text]

    def bounds(self, text, size):
        """Ink box (x0, x1) of text at size, starting at 0 (font units scaled)."""
        scale, x, lo, hi = size / self.upm, 0, None, None
        for name in self._names(text):
            pen = BoundsPen(self.glyphs)
            self.glyphs[name].draw(pen)
            if pen.bounds:
                lo = x + pen.bounds[0] if lo is None else min(lo, x + pen.bounds[0])
                hi = x + pen.bounds[2] if hi is None else max(hi, x + pen.bounds[2])
            x += self.glyphs[name].width
        return lo * scale, hi * scale

    def path(self, text, size, x, baseline):
        """SVG path data of text, its left edge of ink at x, on baseline."""
        scale = size / self.upm
        ink_left = self.bounds(text, size)[0]
        pen = SVGPathPen(self.glyphs)
        advance = 0
        for name in self._names(text):
            # Font units grow upwards, SVG downwards: flip y.
            transform = (scale, 0, 0, -scale, x - ink_left + advance * scale, baseline)
            self.glyphs[name].draw(TransformPen(pen, transform))
            advance += self.glyphs[name].width
        return pen.getCommands()

    def centered(self, text, size, left, top, width, height):
        """Path of text centred in a compartment: by its ink across, by the cap height down
        (so the capitals of a row share one baseline)."""
        x0, x1 = self.bounds(text, size)
        x = left + (width - (x1 - x0)) / 2
        baseline = top + height / 2 + self.cap_height * size / self.upm / 2
        return self.path(text, size, x, baseline)


def _texts():
    """The name in its compartments: S, E, I, T and ON (for SEITON)."""
    return [WORD[0], WORD[1], WORD[2], WORD[3], WORD[4:]]


def compartments(layout):
    """(text, x, y, width, height) of each compartment. "square": S E I on top, T and ON
    below; "shelf": all in one row. ON has a compartment of two, in both."""
    wide = 2 * COL + WALL
    if layout == "square":
        top, bottom = WALL, 2 * WALL + ROW
        cols = [WALL + i * (COL + WALL) for i in range(3)]
        places = [(cols[0], top, COL), (cols[1], top, COL), (cols[2], top, COL),
                  (cols[0], bottom, COL), (cols[1], bottom, wide)]
    else:
        places = [(WALL + i * (COL + WALL), WALL, COL) for i in range(4)] + [(WALL + 4 * (COL + WALL), WALL, wide)]
    return [(text, x, y, w, ROW) for text, (x, y, w) in zip(_texts(), places)]


def shelf_size():
    _t, x, _y, w, _h = compartments("shelf")[-1]
    return x + w + WALL, ROW + 2 * WALL


def _n(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _box(letters: Letters, layout: str, width, height) -> str:
    parts = [f'<rect width="{_n(width)}" height="{_n(height)}" fill="{FRAME}"/>']
    cells = compartments(layout)
    for (_text, x, y, w, h), colour in zip(cells, compartment_colours()):
        parts.append(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" fill="{colour}"/>')
    paths = " ".join(letters.centered(t, LETTER_SIZE, x, y, w, h) for t, x, y, w, h in cells)
    parts.append(f'<path fill="{FRAME}" d="{paths}"/>')
    return "\n  ".join(parts)


def _svg(width, height, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_n(width)} {_n(height)}" '
            f'width="{_n(width)}" height="{_n(height)}">\n  <title>{WORD}</title>\n  {body}\n</svg>\n')


def icon(letters: Letters) -> str:
    return _svg(SIZE, SIZE, _box(letters, "square", SIZE, SIZE))


def wordmark(letters: Letters) -> str:
    """The long logo: the compartments side by side, a shelf."""
    width, height = shelf_size()
    return _svg(width, height, _box(letters, "shelf", width, height))


def icon_small() -> str:
    """16 px on the pixel grid: walls of 1 px across, 2 px between the rows; no letters."""
    cells = [(1, 1, 4, 6), (6, 1, 4, 6), (11, 1, 4, 6), (1, 9, 4, 6), (6, 9, 9, 6)]
    rects = "\n  ".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{colour}"/>'
                        for (x, y, w, h), colour in zip(cells, compartment_colours()))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16" '
            'shape-rendering="crispEdges">\n'
            f'  <title>{WORD}</title>\n  <rect width="16" height="16" fill="{FRAME}"/>\n  {rects}\n</svg>\n')


def _change_size():
    """The picture the change happens in: as wide as the shelf, as high as the box."""
    return shelf_size()[0], SIZE


def placed(layout):
    """(x, y, width, height) of each compartment in the picture of the change, the box or the
    shelf centred in it."""
    width, height = _change_size()
    left, top = ((width - SIZE) / 2, 0) if layout == "square" else (0, (height - shelf_size()[1]) / 2)
    return [(left + x, top + y, w, h) for _t, x, y, w, h in compartments(layout)]


def _middle():
    """Halfway: the rows have parted sideways (across as in the shelf, up and down as in the box)."""
    return [(s[0], b[1], b[2], b[3]) for b, s in zip(placed("square"), placed("shelf"))]


def change_steps():
    """The way from the box to the shelf in steps (start, end): first the rows part sideways -
    the top one to the left, the bottom one to the right - then they close up. So no
    compartment crosses another."""
    return [(placed("square"), _middle()), (_middle(), placed("shelf"))]


def between(a, b, share):
    return tuple(x + (y - x) * share for x, y in zip(a, b))


def change(letters: Letters) -> str:
    """The box turning into the shelf and back, over and over (change_steps); no compartment
    changes its size. The box's frame grows and shrinks with them."""
    width, height = _change_size()
    shelf_w, shelf_h = shelf_size()
    box, middle, shelf = placed("square"), _middle(), placed("shelf")
    # box, hold - part - close up - shelf, hold - part - close up: eased moves, still between
    ease = "0.65 0 0.35 1"
    timing = (f'dur="{CHANGE_SECONDS}s" repeatCount="indefinite" calcMode="spline" '
              f'keyTimes="0;0.25;0.38;0.5;0.75;0.87;1" keySplines="0 0 1 1;{ease};{ease};0 0 1 1;{ease};{ease}"')

    def animate(name, a, m, b):
        values = ";".join(_n(v) for v in (a, a, m, b, b, m, a))
        return f'<animate attributeName="{name}" values="{values}" {timing}/>'

    frame_box = ((width - SIZE) / 2, 0, SIZE, SIZE)
    frame_shelf = (0, (height - shelf_h) / 2, shelf_w, shelf_h)
    frame_middle = (frame_shelf[0], frame_box[1], frame_shelf[2], frame_box[3])
    parts = [f'<rect x="{_n(frame_box[0])}" y="{_n(frame_box[1])}" width="{SIZE}" height="{SIZE}" fill="{FRAME}">'
             + "".join(animate(name, frame_box[k], frame_middle[k], frame_shelf[k])
                       for k, name in enumerate(("x", "y", "width", "height"))) + '</rect>']
    for (text, *_rest), a, m, b, colour in zip(compartments("square"), box, middle, shelf, compartment_colours()):
        parts.append(f'<rect x="{_n(a[0])}" y="{_n(a[1])}" width="{_n(a[2])}" height="{_n(a[3])}" fill="{colour}">'
                     + animate("x", a[0], m[0], b[0]) + animate("y", a[1], m[1], b[1]) + '</rect>')
        moves = [(0, 0), (0, 0), (m[0] - a[0], m[1] - a[1]), (b[0] - a[0], b[1] - a[1])]
        moves += [moves[3], moves[2], moves[0]]
        values = ";".join(f"{_n(dx)} {_n(dy)}" for dx, dy in moves)
        parts.append(f'<g><path fill="{FRAME}" d="{letters.centered(text, LETTER_SIZE, *a)}"/>'
                     f'<animateTransform attributeName="transform" type="translate" values="{values}" {timing}/></g>')
    return _svg(width, height, "\n  ".join(parts))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--font", type=Path, default=FONT)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "assets" / "brand")
    args = parser.parse_args(argv)
    if not args.font.is_file():
        print(f"font not found: {args.font}", file=sys.stderr)
        return 1
    letters = Letters(args.font)
    args.out.mkdir(parents=True, exist_ok=True)
    files = {file_name("icon.svg"): icon(letters), file_name("icon-small.svg"): icon_small(),
             file_name("wordmark.svg"): wordmark(letters), file_name("change.svg"): change(letters)}
    for name, text in files.items():
        (args.out / name).write_text(text, encoding="utf-8")
        print(args.out / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
