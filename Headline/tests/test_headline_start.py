"""How the Headline is started (Headline/Headline.py): the place to start in, and "open the
panel" - at the pointer (--panel) or above the applet's button (--panel --anchor x,y,w,h, in the
device pixels Cinnamon gives; Qt places in logical ones)."""

import pytest

from Headline.Headline import parse_start, to_logical


def test_a_plain_start_in_a_place():
    assert parse_start(["/home/x/Dokumente"]) == ("/home/x/Dokumente", None)


def test_a_plain_start_without_a_place_wants_nothing_shown():
    place, request = parse_start([])
    assert place is None and request is None


def test_the_panel_at_the_pointer():
    assert parse_start(["--panel"]) == (None, {"panel": None})


def test_the_panel_above_the_applets_button():
    assert parse_start(["--panel", "--anchor", "12,1040,36,40"]) == (
        None, {"panel": {"x": 12, "y": 1040, "width": 36, "height": 40}})


@pytest.mark.parametrize("bad", ["12,1040,36", "a,b,c,d", "12,1040,-1,40", ""])
def test_a_broken_anchor_opens_at_the_pointer(bad):
    assert parse_start(["--panel", "--anchor", bad]) == (None, {"panel": None})


def test_device_pixels_to_logical_ones():
    anchor = {"x": 24, "y": 2080, "width": 72, "height": 80}
    assert to_logical(anchor, 2.0) == {"x": 12, "y": 1040, "width": 36, "height": 40}
    assert to_logical(anchor, 1.0) == anchor
    assert to_logical(None, 2.0) is None


def test_started_above_the_roots_it_goes_into_the_first_below(tmp_path):
    from core.brand import META_DIR
    from Headline.Headline import start_place

    (tmp_path / "Dokumente" / META_DIR).mkdir(parents=True)
    (tmp_path / "Dokumente" / META_DIR / "Project.md").write_text("x")
    assert start_place(str(tmp_path)) == str(tmp_path / "Dokumente")
    assert start_place(str(tmp_path / "Dokumente")) == str(tmp_path / "Dokumente")
    (tmp_path / "Leer").mkdir()
    assert start_place(str(tmp_path / "Leer")) == str(tmp_path / "Leer")  # no root: stays
