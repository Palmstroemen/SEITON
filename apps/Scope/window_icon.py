"""The window icon of Scope and SunTree: SEITON's bento box (assets/brand, made by
scripts/make_brand_svgs.py), with its letters in every size: even where they cannot be read they
make it known again."""

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from core.brand import file_name

BRAND = Path(__file__).resolve().parents[2] / "assets" / "brand"
SIZES = (16, 22, 24, 32, 48, 64, 128, 256)


def seiton_icon() -> QIcon:
    """The icon in every size the taskbar may ask for."""
    box = QIcon(str(BRAND / file_name("icon.svg")))
    icon = QIcon()
    for size in SIZES:
        # At factor 1: on a HiDPI screen pixmap(size) answers twice the pixels.
        icon.addPixmap(box.pixmap(QSize(size, size), 1.0))
    return icon
