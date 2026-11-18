"""The Headline remembers where it was (apps/Headline/last_place.py, 2026-11-18): started again
without a place - the restart after an update, the login - it goes back there, not to the
first root (then the clock had no project and counted nothing). The place lies in SEITON's state
folder, beside the clock's; it is no setting."""

import json
from pathlib import Path

from apps.Headline import last_place
from apps.Headline.model import HeadlineModel


def test_it_lies_in_the_state_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    assert last_place.path() == tmp_path / "state" / "seiton" / "headline.json"


def test_written_and_read(tmp_path):
    folder = tmp_path / "Projekte" / "Küche"
    folder.mkdir(parents=True)
    last_place.write(str(folder))
    assert last_place.read() == str(folder)


def test_nothing_remembered_is_none():
    assert last_place.read() is None


def test_a_broken_file_is_none():
    last_place.path().parent.mkdir(parents=True, exist_ok=True)
    for broken in ("not json", json.dumps(["x"]), json.dumps({"place": 5}), json.dumps({"place": "relative/x"})):
        last_place.path().write_text(broken)
        assert last_place.read() is None, broken


def test_a_folder_gone_is_none(tmp_path):
    folder = tmp_path / "weg"
    folder.mkdir()
    last_place.write(str(folder))
    folder.rmdir()
    assert last_place.read() is None


def test_a_place_given_wins(tmp_path):
    remembered, given = tmp_path / "a", tmp_path / "b"
    remembered.mkdir()
    given.mkdir()
    last_place.write(str(remembered))
    assert last_place.start(str(given), lambda place: f"start:{place}") == f"start:{given}"


def test_without_a_place_the_remembered_one(tmp_path):
    remembered = tmp_path / "a"
    remembered.mkdir()
    last_place.write(str(remembered))
    assert last_place.start(None, lambda place: f"start:{place}") == f"start:{remembered}"


def test_without_a_place_and_nothing_remembered_as_before():
    assert last_place.start(None, lambda place: f"start:{place}") == "start:None"


class _Link:
    def call(self, *_a, **_k):
        return {}

    def update_context(self, *_a):
        pass


class _Api:
    def projects_root(self):
        return None


def test_the_model_tells_each_new_place(tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    first.mkdir()
    second.mkdir()
    told = []
    model = HeadlineModel(_Api(), _Link(), str(first), remember=told.append)
    assert model.go(str(second))
    assert told == [str(second.resolve())]
    assert not model.go(str(tmp_path / "missing"))
    assert told == [str(second.resolve())]  # nowhere new
