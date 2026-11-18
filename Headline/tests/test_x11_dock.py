"""The line at the top edge, on X11 (Headline/x11_dock.py; Scope/Designdocument Headline.md, 3):
a dock window - no frame, on every workspace, above the others - which keeps its room with a
strut while it is always there, and keeps none while it hides itself."""

from Headline.x11_dock import apply, strut


def test_the_strut_keeps_the_lines_height_at_the_top_of_its_screen():
    # _NET_WM_STRUT_PARTIAL: left, right, top, bottom, then start and end of each side.
    assert strut((0, 0, 1920, 1080), 30) == [0, 0, 30, 0, 0, 0, 0, 0, 0, 1919, 0, 0]


def test_on_a_second_screen_the_strut_covers_only_that_screen():
    # The root window spans both; the top strut counts from the root's top, its x range is the
    # screen's.
    assert strut((1920, 0, 2560, 1440), 30) == [0, 0, 30, 0, 0, 0, 0, 0, 1920, 4479, 0, 0]


def test_a_screen_lower_than_the_root_top_counts_from_the_root():
    assert strut((0, 200, 1280, 1024), 30)[2] == 230


class _Display:
    def __init__(self):
        self.set = {}
        self.deleted = []
        self.flushed = False

    def intern_atom(self, name):
        return name

    def create_resource_object(self, kind, window_id):
        display = self

        class _Window:
            def change_property(self, prop, type_, fmt, data):
                display.set[prop] = (type_, fmt, list(data))

            def delete_property(self, prop):
                display.deleted.append(prop)

        assert kind == "window" and window_id == 42
        return _Window()

    def flush(self):
        self.flushed = True


def test_always_there_it_is_a_dock_with_a_strut():
    display = _Display()
    apply(display, 42, strut((0, 0, 1920, 1080), 30))
    assert display.set["_NET_WM_WINDOW_TYPE"] == ("ATOM", 32, ["_NET_WM_WINDOW_TYPE_DOCK"])
    assert display.set["_NET_WM_STRUT_PARTIAL"][2] == [0, 0, 30, 0, 0, 0, 0, 0, 0, 1919, 0, 0]
    assert display.set["_NET_WM_STRUT"][2] == [0, 0, 30, 0]  # for older window managers
    assert display.flushed


def test_hiding_itself_it_keeps_no_room():
    display = _Display()
    apply(display, 42, None)
    assert display.set["_NET_WM_WINDOW_TYPE"][2] == ["_NET_WM_WINDOW_TYPE_DOCK"]
    assert set(display.deleted) == {"_NET_WM_STRUT_PARTIAL", "_NET_WM_STRUT"}


def test_scaled_the_strut_is_in_device_pixels():
    # H4 (review 2026-11-18): Qt gives the screen's origin native, its size and the line's
    # height logical; X11 wants device pixels - at a ratio of 2 half the line was kept.
    from Headline.x11_dock import device_strut
    assert device_strut((0, 0, 1920, 1080), 30, 2.0) == strut((0, 0, 3840, 2160), 60)
    assert device_strut((3840, 0, 1280, 720), 30, 1.5) == strut((3840, 0, 1920, 1080), 45)
    assert device_strut((0, 0, 1920, 1080), 30, 1.0) == strut((0, 0, 1920, 1080), 30)
