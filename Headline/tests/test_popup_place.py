"""Popups open towards the room (Headline/popup_place.py; Scope/Designdocument Headline.md, 3):
from the top edge down, from a taskbar at the bottom up, a cascade to the side that has room.
Rectangles are (x, y, width, height); `room` is the screen without the panels
(QScreen.availableGeometry), the anchor may lie outside it (in the Headline's own line or in
the taskbar)."""

from Headline.popup_place import drop, side

SCREEN = (0, 0, 1920, 1080)
BELOW_TASKBAR = (0, 0, 1920, 1040)  # a taskbar of 40 px at the bottom
BELOW_LINE = (0, 30, 1920, 1050)  # the Headline's line of 30 px at the top keeps its room


def test_from_the_top_line_it_drops_down():
    placed = drop((100, 0, 120, 30), (300, 400), BELOW_LINE)
    assert placed == {"x": 100, "y": 30, "direction": "down"}


def test_from_the_taskbar_it_opens_upwards():
    placed = drop((100, 1040, 40, 40), (300, 400), BELOW_TASKBAR)
    assert placed == {"x": 100, "y": 640, "direction": "up"}


def test_it_stays_on_the_screen_at_the_right_edge():
    placed = drop((1850, 0, 60, 30), (300, 400), BELOW_LINE)
    assert placed["x"] == 1920 - 300 and placed["direction"] == "down"


def test_it_stays_on_the_screen_at_the_left_edge():
    placed = drop((-20, 0, 60, 30), (300, 400), BELOW_LINE)
    assert placed["x"] == 0


def test_too_tall_for_either_side_it_takes_the_larger_one_and_is_cut_to_it():
    placed = drop((100, 300, 100, 30), (300, 2000), BELOW_LINE)
    assert placed["direction"] == "down"  # 750 px below, 270 above
    assert placed["y"] == 330 and placed["height"] == 1080 - 330


def test_a_cascade_opens_to_the_right_when_there_is_room():
    placed = side((400, 100, 200, 28), (250, 300), BELOW_LINE)
    assert placed == {"x": 600, "y": 100, "direction": "right"}


def test_a_cascade_turns_left_at_the_right_edge():
    placed = side((1700, 100, 200, 28), (250, 300), BELOW_LINE)
    assert placed == {"x": 1700 - 250, "y": 100, "direction": "left"}


def test_a_cascade_low_on_the_screen_moves_up_to_fit():
    placed = side((400, 1000, 200, 28), (250, 300), BELOW_TASKBAR)
    assert placed["y"] == 1040 - 300 and placed["direction"] == "right"
