"""The Headline's UI strings are English in the code (qsTr); German comes from
i18n/headline_de.ts/.qm, as in Scope and SunTree.

Run scripts/update_translations.py headline after changing strings, and translate new ones."""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTranslator  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

HEADLINE = Path(__file__).resolve().parents[1]
TS = HEADLINE / "i18n" / "headline_de.ts"
QM = HEADLINE / "i18n" / "headline_de.qm"
QSTR = re.compile(r"""\bqsTr\(\s*(["'])((?:\\.|(?!\1).)*)\1""")


def _messages():
    out = []
    for ctx in ET.parse(TS).getroot().iter("context"):
        name = ctx.find("name").text
        for msg in ctx.iter("message"):
            tr = msg.find("translation")
            out.append((name, msg.find("source").text, tr.text or "", tr.get("type") is None))
    return out


def test_every_string_in_the_code_has_a_german_translation():
    finished = {src for _, src, text, done in _messages() if done and text}
    in_code = set()
    for path in HEADLINE.glob("*.qml"):
        in_code |= {m.group(2) for m in QSTR.finditer(path.read_text(encoding="utf-8"))}
    assert "Perspectives" in in_code  # the pattern still finds the strings
    missing = sorted(in_code - finished)
    assert not missing, f"untranslated (run scripts/update_translations.py headline): {missing}"


def test_compiled_translations_match_the_ts():
    QGuiApplication.instance() or QGuiApplication([])
    translator = QTranslator()
    assert translator.load(str(QM))
    stale = [(c, s) for c, s, t, done in _messages() if done and translator.translate(c, s) != t]
    assert not stale, f"headline_de.qm is out of date (run scripts/update_translations.py headline): {stale}"
