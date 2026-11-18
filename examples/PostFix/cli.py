"""CLI entrypoint for PostFix."""

import argparse
import signal
import sys
from pathlib import Path
from typing import Optional

# Started as a script (python3 examples/PostFix/cli.py): make the repo root importable for
# `core`, as apps/Scope/Scope.py does. As a module (python3 -m examples.PostFix.main) it already is.
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.brand import getenv

try:
    from .single_instance import InstanceServer, hand_over, server_name
except ImportError:
    from single_instance import InstanceServer, hand_over, server_name


def _language_setting() -> str:
    """The language set in Setup (General/language), else German (R1)."""
    try:
        from core.settings import Settings

        value = str(Settings().get("General/language") or "de")
    except Exception:
        return "de"
    return value if value in ("de", "en") else "de"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PostFix Markdown editor")
    parser.add_argument("path", nargs="?", help="Markdown file to open")
    parser.add_argument(
        "--lang",
        choices=["de", "en"],
        default=getenv("UI_LANG", "") or _language_setting(),
        help="UI language (de or en)",
    )
    return parser


def note_to_open(path: Optional[str]) -> Optional[Path]:
    """The note a start asks for. One not there yet (postfix neu.md) is made empty in its folder,
    as an editor does: else the running PostFix refused it, a second one started, and what was
    typed into its window had no file to go to."""
    if not path:
        return None
    candidate = Path(path).expanduser()
    if candidate.suffix.lower() != ".md":
        return None
    if not candidate.exists() and candidate.parent.is_dir():
        try:
            candidate.touch(exist_ok=True)
        except OSError:
            pass
    return candidate


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    # The settings under the former name first: else this start wrote the new folder (D5).
    from core.name_migration import take_over_old_config
    take_over_old_config()

    open_path = note_to_open(args.path)

    # One PostFix for all notes (single_instance.py): a later start hands its note over and ends
    # - before loading the rest of PostFix, which only the running one needs.
    single = getenv("POSTFIX_SINGLE", "1") != "0"
    if single and hand_over(server_name(), str(open_path.resolve()) if open_path else None):
        return 0

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    try:
        from .main import PostFixWindow
    except ImportError:
        from main import PostFixWindow

    app = QApplication(sys.argv)
    app.setApplicationName("PostFix")
    app.setOrganizationName("PostFixDev")
    icon_path = Path(__file__).with_name("icons").joinpath("postit.svg")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    def new_window(path):
        return PostFixWindow(
            open_path=path,
            ui_language=args.lang,
        )

    windows = []

    def open_window(path):
        """A note in a window of its own - or, if it is open already, that window to the front."""
        target = Path(path).resolve() if path else None
        for window in windows:
            current = getattr(window.editor, "current_path", None)
            if target and current and Path(current).resolve() == target:
                window.showNormal()
                window.raise_()
                window.activateWindow()
                return window
        window = new_window(target)
        window.setAttribute(Qt.WA_DeleteOnClose)  # a closed note's window really goes
        windows.append(window)
        window.destroyed.connect(lambda _obj=None, w=window: windows.remove(w) if w in windows else None)
        window.show()
        print(f"[PostFix] opened {target}", file=sys.stderr, flush=True)
        return window

    # Asked to end (SIGTERM, e.g. "Bin fertig" on the test machine): close every note as the
    # user would - pending edits saved, the connection cleaned up - instead of dying mid-way.
    # Python only sees the signal while it runs; a quiet timer lets it run now and then.
    signal.signal(signal.SIGTERM, lambda *_: app.closeAllWindows())
    from PySide6.QtCore import QTimer

    signal_check = QTimer(app)
    signal_check.timeout.connect(lambda: None)
    signal_check.start(300)

    if single:  # this one is the PostFix now: it takes the notes of later starts
        server = InstanceServer(server_name(), app)
        server.listen()
        server.openRequested.connect(open_window)

    open_window(open_path)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
