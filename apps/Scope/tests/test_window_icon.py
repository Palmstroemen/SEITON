"""The window icon of Scope and SunTree is SEITON's box (assets/brand, made by
scripts/make_brand_svgs.py), with its letters in every size: even unreadable they make it known."""

import os
import sys
from pathlib import Path

import pytest

SCOPE_DIR = Path(__file__).resolve().parents[1]
REPO = SCOPE_DIR.parents[1]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QColor, QGuiApplication  # noqa: E402

sys.path.insert(0, str(REPO))
from apps.Scope.window_icon import SIZES, seiton_icon  # noqa: E402

FRAME = QColor("#16130f")
LOUD_RED = QColor("#e2402b")


@pytest.fixture(scope="module", autouse=True)
def _app():
    return QGuiApplication.instance() or QGuiApplication([])


def _near(colour, wanted, tolerance=6):
    return all(abs(a - b) <= tolerance for a, b in zip(colour.getRgb()[:3], wanted.getRgb()[:3]))


@pytest.mark.parametrize("size", SIZES)
def test_every_size_is_the_black_box_with_the_red_s(size):
    image = seiton_icon().pixmap(size, size).toImage()
    assert image.width() == size and image.height() == size
    assert _near(image.pixelColor(0, 0), FRAME)  # the frame, square to the corner
    s = image.pixelColor(round(size * 0.08), round(size * 0.08))  # top left in the S compartment
    assert _near(s, LOUD_RED, 12)


def _darkest_inside_s(size):
    """The darkest pixel inside the S compartment: the letter, if there is one."""
    image = seiton_icon().pixmap(size, size).toImage()
    box = range(round(size * 0.10), round(size * 0.30))
    return min(image.pixelColor(x, y).value() for x in box for y in range(round(size * 0.10), round(size * 0.45)))


@pytest.mark.parametrize("size", SIZES)
def test_every_size_has_the_letters(size):
    assert _darkest_inside_s(size) < 180  # the S, red alone is far lighter


def test_scope_and_suntree_both_show_it():
    for script in (SCOPE_DIR / "Scope.py", REPO / "examples" / "SunTree" / "SunTree.py"):
        text = script.read_text(encoding="utf-8")
        assert "setWindowIcon(seiton_icon())" in text, script
        assert "folder.svg" not in text[text.index("def main"):], script
