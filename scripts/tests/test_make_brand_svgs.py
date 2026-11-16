"""The brand's pictures: the square bento box, the long shelf, the small form and the change
from one to the other (scripts/make_brand_svgs.py)."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from scripts import make_brand_svgs as brand

SVG = "{http://www.w3.org/2000/svg}"

pytest.importorskip("fontTools")
if not brand.FONT.is_file():
    pytest.skip(f"font not installed: {brand.FONT}", allow_module_level=True)


@pytest.fixture(scope="module")
def letters():
    return brand.Letters(brand.FONT)


def _rects(svg_text):
    root = ET.fromstring(svg_text)
    return root, [r.attrib for r in root.iter(f"{SVG}rect")]


def test_the_compartments_hold_the_name_in_capitals():
    texts = [c[0] for c in brand.compartments("square")]
    assert texts == ["S", "E", "I", "T", "ON"]
    assert [c[0] for c in brand.compartments("shelf")] == texts


def test_the_shelf_is_one_row_and_on_shares_a_compartment():
    cells = brand.compartments("shelf")
    assert len({y for _t, _x, y, _w, _h in cells}) == 1
    widths = [w for _t, _x, _y, w, _h in cells]
    assert widths[:4] == [brand.COL] * 4 and widths[4] == 2 * brand.COL + brand.WALL
    assert brand.shelf_size() == (brand.WALL + 4 * (brand.COL + brand.WALL) + widths[4] + brand.WALL,
                                  brand.ROW + 2 * brand.WALL)


def test_the_square_and_the_shelf_have_the_same_compartments():
    square = {t: (w, h) for t, _x, _y, w, h in brand.compartments("square")}
    shelf = {t: (w, h) for t, _x, _y, w, h in brand.compartments("shelf")}
    assert square == shelf  # so one turns into the other by moving, not by resizing


def test_s_is_loud_red_and_the_others_share_one_lightness_and_colourfulness():
    colours = brand.compartment_colours()
    assert colours[0] == brand.LOUD_RED
    for colour in colours[1:]:  # within what 8 bits per channel allow
        lightness, chroma, _hue = brand.oklch_of(colour)
        assert lightness == pytest.approx(brand.LIGHTNESS, abs=0.005)
        assert chroma == pytest.approx(brand.CHROMA, abs=0.005)
    assert len(set(colours)) == 5


def test_every_colour_fits_on_a_screen():
    for hue in brand.HUES[1:]:
        assert brand.max_chroma(brand.LIGHTNESS, hue) >= brand.CHROMA - 0.001


def test_the_icon_is_the_black_box_with_coloured_compartments(letters):
    root, rects = _rects(brand.icon(letters))
    assert root.get("viewBox") == f"0 0 {brand.SIZE} {brand.SIZE}"
    assert rects[0]["fill"] == brand.FRAME
    assert [r["fill"] for r in rects[1:]] == brand.compartment_colours()
    assert root.find(f"{SVG}path").get("fill") == brand.FRAME  # the letters, all dark


def test_the_wordmark_is_the_shelf(letters):
    root, rects = _rects(brand.wordmark(letters))
    width, height = brand.shelf_size()
    assert root.get("viewBox") == f"0 0 {brand._n(width)} {brand._n(height)}"
    assert [r["fill"] for r in rects[1:]] == brand.compartment_colours()
    assert len({r["y"] for r in rects[1:]}) == 1


def test_the_small_form_has_the_colours_but_no_letters():
    root, rects = _rects(brand.icon_small())
    assert rects[0]["fill"] == brand.FRAME
    assert [r["fill"] for r in rects[1:]] == brand.compartment_colours()
    assert root.find(f"{SVG}path") is None


def test_the_change_moves_the_compartments_from_square_to_shelf_and_back(letters):
    root = ET.fromstring(brand.change(letters))
    moves = [a for a in root.iter(f"{SVG}animate") if a.get("attributeName") in ("x", "y")]
    assert moves  # the compartments move
    assert root.findall(f".//{SVG}animateTransform")  # and the letters with them


def _overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


@pytest.mark.parametrize("share", [i / 20 for i in range(21)])
def test_no_compartment_crosses_another_on_the_way(share):
    # first the rows part sideways (top to the left, bottom to the right), then they close up
    for step in brand.change_steps():
        cells = [brand.between(a, b, share) for a, b in zip(step[0], step[1])]
        for i in range(len(cells)):
            for j in range(i + 1, len(cells)):
                assert not _overlap(cells[i], cells[j])


def test_the_way_begins_at_the_box_and_ends_at_the_shelf():
    steps = brand.change_steps()
    assert steps[0][0] == brand.placed("square") and steps[-1][1] == brand.placed("shelf")
    for (_a, end), (start, _b) in zip(steps, steps[1:]):
        assert end == start


def test_main_writes_the_four_pictures(tmp_path):
    assert brand.main(["--out", str(tmp_path)]) == 0
    names = sorted(p.name for p in Path(tmp_path).iterdir())
    assert names == ["seiton-change.svg", "seiton-icon-small.svg", "seiton-icon.svg", "seiton-wordmark.svg"]
