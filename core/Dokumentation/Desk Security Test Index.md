# Desk Security Test Index

This file tracks security-relevant coverage for the `Desk.md` system.

## 1) Covered Attack Classes

### A. Path traversal / filename injection
- Rejects unsafe config names like `../outside.md`, separators, and spoofed names.
- Rejects overlong config names.
- Coverage:
  - `core/tests/unit/test_scope_api_tags.py`
  - `core/tests/unit/test_desk_service.py`

### B. Filter desk escape attempts
- Rejects filter-linked desk references (`## Desk` in a filter) escaping the filter's base directory.
- Coverage:
  - `core/tests/unit/test_desk_runtime_api.py`
  - `core/tests/unit/test_desk_config.py`

### C. Symlink-based profile escape
- Rejects symlinked `Desk.md` files during desk profile parsing.
- Coverage:
  - `core/tests/unit/test_desk_config.py`

### D. Wallpaper path abuse
- Relative wallpaper presets must remain inside profile directory.
- Relative symlink escape is rejected.
- Relative symlink inside profile is accepted.
- Explicit wallpaper path is treated as intentional user override.
- Coverage:
  - `core/tests/unit/test_desk_runtime_api.py`

### E. Command execution abuse
- Dry-run mode does not execute subprocesses.
- Argument boundaries preserved (no shell splitting; payload remains one argument).
- Timeout and OSError are handled without crashing runtime flow.
- Unsafe theme and program names (leading `-`, quotes, control characters) are refused without running anything (Cinnamon/GNOME backend).
- Cinnamon taskbar: dry run and symlinked applet settings files change nothing.
- Coverage:
  - `core/tests/unit/test_desk_runtime_api.py`
  - `core/tests/unit/test_desktop_backend_gnome.py`

### F. Parser robustness / malformed input
- Fuzz-like randomized Desk payloads and markdown content do not crash parser/resolver.
- `inherit` normalization remains within allowed values.
- Coverage:
  - `core/tests/unit/test_desk_config.py`

### G. Runtime context robustness
- Invalid path input does not crash context handling.
- Runtime reports controlled `invalid_path` / `runtime_error`.
- Coverage:
  - `core/tests/unit/test_desk_runtime_api.py`
  - `core/tests/unit/test_scope_api_tags.py`

### H. Following the projects without touching the real desktop
- A fake backend stands in for the desktop; the tests use their own config home, so `~/.config/seiton` is never touched.
- Writing a `Desk.md` keeps other lines and refuses symlinks; a desk that cannot be written does not stop following.
- Coverage:
  - `core/tests/unit/test_desk_follow.py`

## 2) Current Security Notes in Code

Security comments have been added at enforcement points, for example:
- `core/desk.py`
- `core/desk_runtime.py`
- `core/desk_service.py`
- `core/scope_api.py`
- `core/desktop_backends/command.py`
- `core/desktop_backends/gnome.py`

These comments use the required prefix:
- `# Security: ...`

## 3) Suggested Next Hardening Steps

1. Add TOCTOU-focused tests around file existence changes between validation and command execution for wallpaper files.
2. Add high-volume fuzz corpus for markdown parser edge cases (long unicode sequences, repeated mixed sections).
3. Add optional policy mode for explicit wallpaper paths (`strict_relative_only` vs `allow_explicit_absolute`).
4. Done: context switching with desk runtime enabled and backend mocked (`core/tests/unit/test_desk_follow.py`, including Scope and PostFix sharing what was set last).

## 4) Quick Status

- Desk security suite status (run 2026-11-18): the six files below, 129 tests passing.
- Primary desk security test files:
  - `core/tests/unit/test_desk_config.py`
  - `core/tests/unit/test_desk_runtime_api.py`
  - `core/tests/unit/test_desk_service.py`
  - `core/tests/unit/test_desk_follow.py`
  - `core/tests/unit/test_desktop_backend_gnome.py`
  - `core/tests/unit/test_scope_api_tags.py`
