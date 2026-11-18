"""Colours worked out from a few base values (core/color_derive.py; apps/Scope/Colour inventory.md,
apps/Scope/Designdocument Setup.md, 5): a clean ladder instead of 79 colours set by hand."""

import re

import pytest

from core.color_derive import (
    Base,
    contrast,
    derive,
    from_hex,
    is_dark,
    oklch_of,
    to_hex,
)
from core.color_schemes import shipped_scheme

# The base values the systems around us give (Linux Mint 21.3, Mint-L-Darker-Aqua, read
# 2026-11-15), and a dark and a gaudy one, so the rules are not fitted to one case.
MINT = Base(background="#f9f9f9", text="#303030", content="#f9f9f9", accent="#6cabcd")
DARK_SYSTEM = Base(background="#202124", text="#e8eaed", content="#18191b", accent="#8ab4f8")
GAUDY = Base(background="#fff6e0", text="#3a1f00", content="#ffffff", accent="#e0218a")
TODAY_DARK = Base(background="#0f1014", text="#e6e6e6", content="#0f1117", accent="#4a5675",
                  tint=(270.0, 0.02))
TODAY_LIGHT = Base(background="#f3f4f8", text="#1f2433", content="#ffffff", accent="#9fb1dd",
                   tint=(270.0, 0.012))
ALL = {"mint": MINT, "dark system": DARK_SYSTEM, "gaudy": GAUDY,
       "today dark": TODAY_DARK, "today light": TODAY_LIGHT}

_COLOR = re.compile(r"#([0-9a-f]{2})?[0-9a-f]{6}")


def L(value):
    return oklch_of(value)[0]


# --- the arithmetic ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", ["#000000", "#ffffff", "#0f1014", "#6cabcd", "#e0218a", "#808080"])
def test_hex_survives_the_way_through_oklch(value):
    assert to_hex(*from_hex(value)) == value


def test_alpha_stands_in_front_as_in_qt():
    assert to_hex(*from_hex("#579499a3")) == "#579499a3"
    assert from_hex("#579499a3")[3] == pytest.approx(0x57 / 255)


def test_contrast_is_wcags():
    assert contrast("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast("#777777", "#777777") == pytest.approx(1.0)


def test_light_or_dark_comes_from_the_colours_not_from_a_name():
    assert not is_dark(MINT)
    assert is_dark(DARK_SYSTEM)
    assert is_dark(TODAY_DARK)
    assert not is_dark(GAUDY)


# --- what every scheme worked out must hold ---------------------------------------------------

@pytest.mark.parametrize("name", ALL)
def test_it_names_exactly_the_colours_of_the_schemes(name):
    assert derive(ALL[name]).keys() == shipped_scheme("dark").keys()


@pytest.mark.parametrize("name", ALL)
def test_every_value_is_a_colour(name):
    for colour, value in derive(ALL[name]).items():
        assert _COLOR.fullmatch(value), (colour, value)


@pytest.mark.parametrize("name", ALL)
@pytest.mark.parametrize("text, back", [
    ("text", "bg"), ("text", "panel"), ("text", "pill"), ("smallButtonText", "smallButtonBg"),
    ("setupText", "setupPanel"), ("setupMuted", "setupPanel"),
    ("dialogTextStrong", "dialogPanelBg"), ("dialogInputText", "dialogInputBg"),
    ("aclDialogText", "aclDialogBg"),
    ("crownText", "crownFolderOwn"), ("crownText", "crownFolderSystem"),
    ("stemText", "stemFolder"), ("stemClipboardText", "stemClipboard"),
    ("noticeText", "noticeBack"), ("lensOffText", "lensOff"), ("lensLevelText", "lensLevel"),
])
def test_text_stays_readable(name, text, back):
    colours = derive(ALL[name])
    assert contrast(colours[text], colours[back]) >= 4.5, (text, colours[text], back, colours[back])


@pytest.mark.parametrize("name", ALL)
def test_side_texts_are_softer_but_readable(name):
    colours = derive(ALL[name])
    for soft in ("setupMuted", "dialogTextMuted", "stemSubText"):
        back = {"setupMuted": "setupPanel", "dialogTextMuted": "dialogPanelBg", "stemSubText": "stemFolder"}[soft]
        strong = {"setupMuted": "setupText", "dialogTextMuted": "dialogTextStrong", "stemSubText": "stemText"}[soft]
        assert 3.0 <= contrast(colours[soft], colours[back]) < contrast(colours[strong], colours[back]), soft


@pytest.mark.parametrize("name", ALL)
def test_surfaces_climb_from_the_background_towards_the_text(name):
    colours = derive(ALL[name])
    ladder = ["bg", "panelAlt", "panel", "pill", "smallButtonBg"]
    towards = 1 if is_dark(ALL[name]) else -1
    steps = [towards * (L(colours[b]) - L(colours[a])) for a, b in zip(ladder, ladder[1:])]
    assert all(step > 0.005 for step in steps), list(zip(ladder[1:], steps))


@pytest.mark.parametrize("name", ALL)
def test_a_border_stands_out_from_its_surface(name):
    colours = derive(ALL[name])
    for surface in ("pill", "smallButtonBg", "smallButtonActiveBg", "setupPill", "dialogPanelBg"):
        border = surface[:-2] + "Border" if surface.endswith("Bg") else surface + "Border"
        assert abs(L(colours[border]) - L(colours[surface])) >= 0.05, (surface, border)


def test_dark_takes_larger_steps_than_light():
    def first_step(base):
        colours = derive(base)
        return abs(L(colours["panel"]) - L(colours["bg"]))
    assert first_step(DARK_SYSTEM) > first_step(MINT)


@pytest.mark.parametrize("name", ALL)
def test_the_folder_rows_tones_climb_in_one_order(name):
    colours = derive(ALL[name])
    towards = 1 if is_dark(ALL[name]) else -1
    path, current, folders = (L(colours[c]) for c in ("folderPathTint", "folderCwpTint", "folderULineTint"))
    assert towards * (current - path) > 0.03 and towards * (folders - current) > 0.03


# --- where the hues come from (decided 2026-11-15) --------------------------------------------

def test_under_the_system_the_surfaces_are_neutral():
    colours = derive(MINT)
    for surface in ("bg", "panel", "panelAlt", "pill", "smallButtonBg", "setupPanel", "noticeBack",
                    "dialogPanelBg", "aclDialogBg", "folderPathTint", "stemFolder"):
        assert oklch_of(colours[surface])[1] < 0.004, surface


def test_a_scheme_of_ones_own_may_have_a_tint():
    colours = derive(TODAY_DARK)
    for surface in ("panel", "pill", "dialogPanelBg", "noticeBack"):
        chroma, hue = oklch_of(colours[surface])[1:3]
        assert chroma > 0.008 and abs(hue - 270) < 8, surface


@pytest.mark.parametrize("name", ALL)
def test_active_and_selected_take_the_accent(name):
    colours = derive(ALL[name])
    hue = oklch_of(ALL[name].accent)[2]
    for active in ("accentSecondary", "smallButtonActiveBg", "stemCurrent", "crownFolderOwn",
                   "dropHighlight", "fileSelectionFill", "noticeUndo"):
        assert abs((oklch_of(colours[active])[2] - hue + 180) % 360 - 180) < 6, active


@pytest.mark.parametrize("name", ALL)
def test_what_seiton_brings_is_the_accent_turned(name):
    colours = derive(ALL[name])
    hue = (oklch_of(ALL[name].accent)[2] - 45) % 360
    for system in ("crownFolderSystem", "crownBackSystem", "lensLevel", "lensLevelBorder"):
        assert abs((oklch_of(colours[system])[2] - hue + 180) % 360 - 180) < 6, system


@pytest.mark.parametrize("name", ALL)
def test_the_lens_and_errors_keep_their_hue(name):
    colours = derive(ALL[name])
    assert colours["lensFrame"] == "#d97706"
    assert colours["dialogError"] == "#b00020"
    for lens in ("lensOff", "lensOffHover"):
        assert abs(oklch_of(colours[lens])[2] - 75) < 8, lens


# --- the dialogs, the ACL dialogs and the notice ----------------------------------------------

@pytest.mark.parametrize("name", ALL)
def test_dialogs_are_the_scheme_turned_over(name):
    colours = derive(ALL[name])
    dark = is_dark(ALL[name])
    for back in ("dialogPanelBg", "dialogInputBg", "aclDialogBg"):
        assert (L(colours[back]) > 0.8) == dark, back


@pytest.mark.parametrize("name", ALL)
def test_the_acl_dialogs_are_dialogs_like_the_others(name):
    colours = derive(ALL[name])
    assert colours["aclDialogBg"] == colours["dialogPanelBg"]
    assert colours["aclDialogText"] == colours["dialogTextStrong"]
    assert colours["aclDialogMuted"] == colours["dialogTextMuted"]


@pytest.mark.parametrize("name", ALL)
def test_the_notice_is_dark_on_any_desktop(name):
    colours = derive(ALL[name])
    assert L(colours["noticeBack"]) < 0.35 and L(colours["noticeText"]) > 0.85


# --- the room and the overlays ----------------------------------------------------------------

@pytest.mark.parametrize("name", ALL)
def test_the_files_area_is_the_content_background(name):
    # the room (a project's colour) is laid over it at run time, by the slider (step 4)
    assert derive(ALL[name])["filesPanelCenter"] == ALL[name].content.lower()


@pytest.mark.parametrize("name", ALL)
def test_text_on_the_accent_is_black_or_white_whichever_reads(name):
    colours = derive(ALL[name])
    on = colours["accentPrimaryText"]
    assert on in ("#ffffff", "#000000")
    other = "#000000" if on == "#ffffff" else "#ffffff"
    assert contrast(on, colours["smallButtonActiveBg"]) >= contrast(other, colours["smallButtonActiveBg"])


@pytest.mark.parametrize("name", ALL)
def test_overlays_are_see_through(name):
    colours = derive(ALL[name])
    for overlay in ("stemTint", "crownFolderLine", "crownEmbryoLine", "fileSelectionFill",
                    "selectionBoxFill", "dropHighlight"):
        assert len(colours[overlay]) == 9 and colours[overlay][1:3] != "ff", overlay
