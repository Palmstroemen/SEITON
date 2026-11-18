# SEITON Development Guide

## Design Docs

- [Designdocument Projects](../core/Dokumentation/Designdocument%20Projects.md)
- [Designdocument BlueprintLayer](../core/Dokumentation/Designdocument%20BlueprintLayer.md)
- [Designdocument ACLs](../core/Dokumentation/Designdocument%20ACLs.md)
- [Designdocument Tags](../core/Dokumentation/Designdocument%20Tags.md)
- [Designdocument Export-Import](../core/Dokumentation/Designdocument%20Export-Import.md)
- [Designdocument Time](../core/Dokumentation/Designdocument%20Time.md) (time tracking)
- [Designdocument Headline](../Scope/Designdocument%20Headline.md)
- [Designdocument Setup](../Scope/Designdocument%20Setup.md)
- [Designdocument Krone](../SunTree/Designdocument%20Krone.md) (SunTree)

## Repository Structure

```
SEITON/
├── core/                 # API, FUSE layer, project config, ACLs
├── core/Dokumentation/   # Design documents
├── Scope/                # QML GUI file browser
├── Headline/             # the line at the top edge (replaces Scope's minimal view M)
├── Time/                 # the time tracking's screen
├── SunTree/              # the crown, for dropping into folders
├── PostFix/              # Markdown editor
├── cli/                  # CLI tools (myls, myproject, mytag, etc.), see cli/Dokumentationen/CLI.md
├── daemon/               # the lens drive's daemon, the clock
├── cloud/                # Nextcloud app and the core service
├── installer/            # seiton_install.py (./install.sh) and its requirements
├── scripts/              # translations, test machine, tutorial data
├── templates/            # the templates the installer copies to ~/.seiton/Templates
├── Learning SEITON/      # the tutorial
├── docs/                 # Consolidated documentation
└── LICENSE
```

`SEITON_Test/` (test and demo data) is local and not in git.

## Development Environment Setup

### Dependencies

```bash
./install.sh
~/.local/share/seiton/venv/bin/pip install -r requirements-dev.txt
```

`./install.sh` installs the system packages (libfuse 2, bubblewrap, ...) and SEITON's own venv
(`~/.local/share/seiton/venv`) with `installer/requirements.txt`; a plain `pip install` into
the system Python is refused on newer distributions (PEP 668). The tutorial's example data also
needs `reportlab` in that venv (`pip install reportlab`); without it its tests are skipped.

`requirements-full.txt` still points to `core/requirements.txt`, a second, older list (other Qt
version, `pynput` with its dependencies). Use `installer/requirements.txt`.

### Run Tests

```bash
# All tests (every test folder, see pytest.ini), from the repository root
python3 -m pytest

# Core only
python3 -m pytest core/tests/unit/

# CLI only
python3 -m pytest cli/tests/

# PostFix only
python3 -m pytest PostFix/tests/

# Benchmarks (timing, depends on the machine; not in the normal run)
python3 -m pytest core/tests/unit -m benchmark
```

`python3` here is the venv's: `~/.local/share/seiton/venv/bin/python -m pytest`, or activate
the venv first. Qt runs offscreen in the tests (`conftest.py`). The Nextcloud tests
(`cloud/nextcloud/tests`) need a test server and skip without one.

### Launch Applications

```bash
python3 Scope/Scope.py
python3 PostFix/cli.py path/to/file.md
python3 Headline/Headline.py
python3 SunTree/SunTree.py SEITON_Test/Projekte/
python3 cli/myls.py SEITON_Test/Projekte/ --extended
```

After `./install.sh` the same as launchers in `~/.local/bin`: `seiton`, `seiton-postfix`,
`seiton-headline`, `seiton-time`, `seiton-clock`, the CLI tools.

## UI Language (i18n)

UI strings in the code are **English** (`qsTr("…")` in QML/JS, `self.tr("…")` in Python);
every other language is a translation:

- `Scope/i18n/scope_de.ts`, `PostFix/i18n/postfix_de.ts`, `SunTree/i18n/suntree_de.ts`,
  `Headline/i18n/headline_de.ts`, `Time/i18n/time_de.ts` — German translations
  (source), compiled to the `.qm` files the apps load.
- After adding or changing strings run `python3 scripts/update_translations.py`: it
  extracts the strings (new ones arrive as "unfinished"), keeps existing translations and
  rebuilds the `.qm`. Translate the unfinished entries (e.g. Qt Linguist) and run it again.
- Language: `SEITON_UI_LANG` (default `de`; the former `MYOS_UI_LANG` is still read); English
  needs no file.
- The `test_*_i18n.py` tests of each app fail when a string has no German translation or a
  `.qm` is out of date.

## Security

- Path traversal protection in embryo paths and API
- ACL system: `off` / `monitor` / `enforce` (`SEITON_ACL_MODE`, see [ACL_ROLLOUT.md](../core/Dokumentation/ACL_ROLLOUT.md))
- Test in user space; do not run FUSE as root

## Contribution Guidelines

1. Discuss changes via GitHub issue first
2. Small, focused pull requests
3. Add tests for new features
4. Update documentation

---

*Last verified: 2026-11-18*
