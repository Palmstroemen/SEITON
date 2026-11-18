"""All tests share one Qt application, made by the root conftest.py: a QApplication, so that
widgets (PostFix's editor) work after tests that only asked for a QGuiApplication. Without it,
one pytest run over all folders aborted ("Cannot create a QWidget without QApplication")."""

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication


def test_the_one_application_can_make_widgets():
    assert isinstance(QGuiApplication.instance(), QApplication)


def test_tests_draw_without_a_screen():
    assert QGuiApplication.platformName() == "offscreen"
