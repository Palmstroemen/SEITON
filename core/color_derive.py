"""Colours worked out from a few base values (apps/Scope/Colour inventory.md; Scope/Designdocument
Setup.md, 5).

Base values: background, text, content background, accent, and for a scheme of one's own a tint.
From them every colour of the schemes follows, worked out in OKLCH (lightness L, chroma C, hue h),
so the shades fit together under any system's colours and the texts stay readable:

- a ladder of surfaces from the background towards the text, in steps; a step in a dark scheme is
  larger than in a light one (on dark, the eye needs more to see a difference);
- mid tones and side texts as a share of the way from the background to the text;
- hues: none (the system's greys) or the tint for surfaces, the accent for what is active or
  selected, the accent turned by -45 degrees for what SEITON brings, fixed for the lens (amber)
  and for errors (red);
- the dialogs are the same ladder turned over; the notice after a drop is always dark.

No Qt here: the programs hand in the base values (from QPalette or a scheme of one's own) and
take the colours by name, as from a scheme file. Colours are written as Qt writes them: #rrggbb,
or #aarrggbb with the opacity in front.
"""

import math
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

# --- OKLCH ------------------------------------------------------------------------------------


def _to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _from_linear(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _parse(value: str) -> Tuple[float, float, float, float]:
    digits = value.strip().lstrip("#")
    alpha = 1.0
    if len(digits) == 8:
        alpha, digits = int(digits[:2], 16) / 255, digits[2:]
    r, g, b = (int(digits[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return r, g, b, alpha


def _rgb_to_oklab(r: float, g: float, b: float) -> Tuple[float, float, float]:
    r, g, b = _to_linear(r), _to_linear(g), _to_linear(b)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def _oklab_to_linear_rgb(L: float, a: float, b: float) -> Tuple[float, float, float]:
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def from_hex(value: str) -> Tuple[float, float, float, float]:
    """(L, C, h, alpha) of a colour written as Qt writes it."""
    r, g, b, alpha = _parse(value)
    L, a, b_ = _rgb_to_oklab(r, g, b)
    return L, math.hypot(a, b_), math.degrees(math.atan2(b_, a)) % 360, alpha


def oklch_of(value: str) -> Tuple[float, float, float]:
    return from_hex(value)[:3]


def _in_gamut(rgb: Tuple[float, ...]) -> bool:
    return all(-1e-6 <= c <= 1 + 1e-6 for c in rgb)


def to_hex(L: float, C: float, h: float, alpha: float = 1.0) -> str:
    """The colour (L, C, h); a chroma the screen cannot show is lowered until it can, the hue and
    the lightness stay."""
    L = min(max(L, 0.0), 1.0)

    def rgb(chroma: float) -> Tuple[float, float, float]:
        rad = math.radians(h)
        return _oklab_to_linear_rgb(L, chroma * math.cos(rad), chroma * math.sin(rad))

    if not _in_gamut(rgb(C)):
        low, high = 0.0, C
        for _ in range(24):
            mid = (low + high) / 2
            low, high = (mid, high) if _in_gamut(rgb(mid)) else (low, mid)
        C = low
    channels = "".join(f"{round(min(max(_from_linear(c), 0.0), 1.0) * 255):02x}" for c in rgb(C))
    opacity = round(min(max(alpha, 0.0), 1.0) * 255)
    return f"#{channels}" if opacity == 255 else f"#{opacity:02x}{channels}"


def _luminance(value: str) -> float:
    r, g, b, _ = _parse(value)
    return 0.2126 * _to_linear(r) + 0.7152 * _to_linear(g) + 0.0722 * _to_linear(b)


def contrast(one: str, other: str) -> float:
    """WCAG's contrast ratio, 1 to 21 (opacity left out)."""
    a, b = sorted((_luminance(one), _luminance(other)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def _normal(value: str) -> str:
    return to_hex(*from_hex(value))


# --- base values ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Base:
    background: str
    text: str
    content: str  # lists, cards, the files area: QPalette.Base
    accent: str  # QPalette.Accent, else Highlight
    tint: Optional[Tuple[float, float]] = None  # (hue, chroma) of the surfaces; None: neutral


def is_dark(base: Base) -> bool:
    """Light or dark from the colours themselves, never from a theme's name (Qt says Dark for
    Mint-L-Darker-Aqua, a light theme: Designdocument Setup.md, 5)."""
    return oklch_of(base.text)[0] > oklch_of(base.background)[0]


# The rules' numbers. A step is in OKLCH lightness; a share is of the way from background to text.
STEP_DARK = 0.035
STEP_LIGHT = 0.02
BORDER = 0.08  # a border lies this much further towards the text than its surface
ACCENT_SOFT = 0.06  # chroma of active and selected surfaces
SEITON_TURN = -45.0  # what SEITON brings: the accent's hue turned by this
LENS_HUE = 75.0
LENS_FRAME = "#d97706"
ERROR = "#b00020"
# The turned-over side (dialogs) and the notice, as lightness of background and text.
LIGHT_SIDE = (0.97, 0.25)
DARK_SIDE = (0.23, 0.95)


class _Ladder:
    """One side's ladder: background and text lightness, step, the hues to use."""

    def __init__(self, back: float, text: float, tint: Tuple[float, float], accent: Tuple[float, float]):
        self.back, self.text = back, text
        self.towards = 1.0 if text > back else -1.0
        self.step = STEP_DARK if text > back else STEP_LIGHT
        self.tint_hue, self.tint_chroma = tint
        self.accent_hue, self.accent_chroma = accent

    # lightness
    def up(self, steps: float) -> float:
        return self.back + self.towards * steps * self.step

    def share(self, part: float) -> float:
        return self.back + part * (self.text - self.back)

    def border(self, lightness: float) -> float:
        return lightness + self.towards * BORDER

    # colours
    def surface(self, lightness: float) -> str:
        return to_hex(lightness, self.tint_chroma, self.tint_hue)

    def neutral(self, lightness: float) -> str:
        return to_hex(lightness, 0.0, 0.0)

    def accented(self, lightness: float, chroma: float = ACCENT_SOFT, alpha: float = 1.0) -> str:
        return to_hex(lightness, min(chroma, self.accent_chroma), self.accent_hue, alpha)

    def seiton(self, lightness: float, chroma: float) -> str:
        return to_hex(lightness, chroma, (self.accent_hue + SEITON_TURN) % 360)

    def lens(self, lightness: float, chroma: float) -> str:
        return to_hex(lightness, chroma, LENS_HUE)


def _black_or_white(back: str) -> str:
    return "#ffffff" if contrast("#ffffff", back) >= contrast("#000000", back) else "#000000"


def derive(base: Base) -> Dict[str, str]:
    """Every colour of the schemes (core/schemes/*.json names them), worked out from base."""
    back_l, text_l = oklch_of(base.background)[0], oklch_of(base.text)[0]
    accent_l, accent_c, accent_h = oklch_of(base.accent)
    tint = base.tint or (0.0, 0.0)
    accent = (accent_h, accent_c)
    m = _Ladder(back_l, text_l, tint, accent)  # the scheme itself
    d = _Ladder(*(LIGHT_SIDE if m.towards > 0 else DARK_SIDE), tint, accent)  # turned over
    n = _Ladder(*DARK_SIDE, tint, accent)  # the notice: dark on any desktop
    text = _normal(base.text)
    content = _normal(base.content)
    c: Dict[str, str] = {}

    # window and rows
    c["bg"] = _normal(base.background)
    c["card"] = content
    c["panelAlt"] = m.surface(m.up(1))
    c["panel"] = m.surface(m.up(2))
    c["pill"] = m.surface(m.up(3))
    c["pillBorder"] = m.surface(m.border(m.up(3)))
    c["smallButtonBg"] = m.surface(m.up(4))
    c["smallButtonBorder"] = m.surface(m.border(m.up(4)))
    c["smallButtonActiveBg"] = m.accented(m.up(6))
    c["smallButtonActiveBorder"] = m.accented(m.border(m.up(6)))
    c["smallButtonText"] = m.surface(m.share(0.85))
    c["accentSecondary"] = m.accented(m.up(5))
    c["accentSecondaryBorder"] = m.accented(m.border(m.up(5)))
    c["text"] = text
    c["accentPrimaryText"] = _black_or_white(c["smallButtonActiveBg"])
    # the folder rows' tones, neutral: a project's colour is laid over them at run time
    c["folderPathTint"] = m.neutral(m.share(0.20))
    c["folderCwpTint"] = m.neutral(m.share(0.32))
    c["folderULineTint"] = m.neutral(m.share(0.44))
    # the files area: the content background; the room is laid over it (the slider, step 4)
    c["filesPanelCenter"] = content
    # marking
    c["fileSelectionFill"] = m.accented(m.share(0.55), 0.05, 0.34)
    c["fileSelectionBorder"] = m.accented(m.share(0.75), 0.05, 0.92)
    c["selectionBoxFill"] = m.accented(m.share(0.65), 0.05, 0.18)
    c["selectionBoxBorder"] = m.accented(m.share(0.85), 0.05, 0.85)
    c["dropHighlight"] = m.accented(0.5, 0.3, 0.5)
    c["lensFrame"] = LENS_FRAME
    c["projectButtonActive"] = _normal(base.accent)  # the room's colour, where there is one
    # the back of Scope
    c["setupText"] = text
    c["setupMuted"] = m.surface(m.share(0.70))
    c["setupPanelDeep"] = m.surface(m.up(1))
    c["setupPanel"] = m.surface(m.up(2))
    c["setupPill"] = m.surface(m.up(4))
    c["setupPillBorder"] = m.surface(m.border(m.up(4)))
    # dialogs: the scheme turned over; the ACL dialogs are dialogs like the others
    c["dialogPanelBg"] = d.surface(d.back)
    c["dialogPanelBorder"] = d.surface(d.border(d.back))
    c["dialogTextStrong"] = d.surface(d.text)
    c["dialogTextMuted"] = d.surface(d.share(0.70))
    c["dialogInputBg"] = d.surface(d.up(-1.5))
    c["dialogInputBorder"] = d.surface(d.share(0.45))
    c["dialogInputText"] = d.surface(d.text)
    c["dialogInputPlaceholder"] = d.surface(d.share(0.55))
    c["dialogError"] = ERROR
    c["aclDialogBg"] = c["dialogPanelBg"]
    c["aclDialogBorder"] = c["dialogPanelBorder"]
    c["aclDialogText"] = c["dialogTextStrong"]
    c["aclDialogMuted"] = c["dialogTextMuted"]
    c["aclSwitchOn"] = d.accented(d.up(6))
    c["aclSwitchOff"] = d.surface(d.up(2))
    c["aclSwitchOffText"] = d.surface(d.share(0.55))
    # SunTree and the small crown
    c["crownBackOwn"] = m.accented(m.up(4), 0.04)
    c["crownBackSystem"] = m.seiton(m.up(4), 0.04)
    c["crownFolderOwn"] = m.accented(m.share(0.34), 0.07)
    c["crownFolderSystem"] = m.seiton(m.share(0.34), 0.06)
    c["crownFolderLine"] = to_hex(*oklch_of(content), 0.9)
    c["crownEmbryoLine"] = to_hex(*oklch_of(text), 0.48)
    c["crownText"] = text
    c["stemFolder"] = m.surface(m.up(5))
    c["stemFolderBorder"] = m.surface(m.share(0.45))
    c["stemText"] = text
    c["stemSubText"] = m.surface(m.share(0.75))
    c["stemCurrent"] = m.accented(m.up(6))
    c["stemCurrentBorder"] = m.accented(m.share(0.70), 0.09)
    c["stemTint"] = to_hex(0.0 if m.towards > 0 else 1.0, 0.0, 0.0, 0.38)
    c["stemPreviewBack"] = m.surface(m.up(3))
    c["stemClipboard"] = m.surface(m.up(4))
    c["stemClipboardBorder"] = m.surface(m.border(m.up(4)))
    c["stemClipboardText"] = text
    # the notice after a drop: dark on any desktop, so it stands out on a light one
    c["noticeBack"] = n.surface(n.back)
    c["noticeBorder"] = n.surface(n.share(0.40))
    c["noticeText"] = n.surface(n.text)
    c["noticeUndo"] = n.accented(n.up(4))
    c["noticeUndoHover"] = n.accented(n.up(7), 0.08)
    c["noticeUndoBorder"] = n.accented(n.share(0.75), 0.09)
    # the lens in SunTree: amber to take it off, SEITON's hue for its levels
    c["lensOff"] = m.lens(m.up(4), 0.03)
    c["lensOffHover"] = m.lens(m.up(7), 0.045)
    c["lensOffText"] = m.lens(text_l, 0.03)
    c["lensLevel"] = m.seiton(m.up(7), 0.045)
    c["lensLevelHover"] = m.seiton(m.up(9.5), 0.05)
    c["lensLevelBorder"] = m.seiton(m.share(0.60), 0.05)
    c["lensLevelText"] = m.seiton(text_l, 0.02)
    return c
