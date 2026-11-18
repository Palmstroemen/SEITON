# SEITON Markdown Thumbnailer

This component adds markdown thumbnails for Linux file browsers that implement
the Freedesktop thumbnailer standard (for example Nautilus, Nemo, Caja).

## Visual behavior

- Short notes (fewer than 10 lines) are rendered as sticky notes (Post-it style).
- Longer notes are rendered as A4 sheets, very long ones (100 lines and more) as notebook pages (Notizblock/Heft style).
- Files inside a `.seiton` folder are rendered as config cards, long chats as speech bubbles.
- If markdown frontmatter contains `background_color: "#rrggbb"`, that color is used.
- Optional frontmatter `note_style` (or the former `myos_note_style`) can override style manually.

## Manual note styles

Supported style values (aliases in German/English are accepted):

- `postit` - short sticky note
- `sheet` / `a4` / `mitschrift` - A4 page style
- `notebook` / `heft` / `konzept` - notebook concept page
- `cloud` / `gedankenskizze` - thought cloud card
- `chat` / `ai-chat` / `sprechblase` - speech bubble style
- `config` / `konfiguration` - config/settings card

## Files

- `core/thumbnailer/markdown_thumbnailer.py` - renderer
- `scripts/seiton_md_thumbnailer.py` - renderer script (entry point)
- `installer/seiton-md.thumbnailer` - thumbnailer template
- `installer/seiton_install.py` - writes it (`./install.sh --thumbnailer`)
- `installer/install-thumbnailer.sh` - older local helper, still works

## Install (per user)

From project root:

```bash
./install.sh --thumbnailer
rm -rf ~/.cache/thumbnails/*
```

This writes `~/.local/share/thumbnailers/seiton-md.thumbnailer` with the Python of SEITON's
venv (which has Pillow). Then restart/reopen your file browser.

## Remove

```bash
./install.sh --uninstall
```

takes it away with everything else the installer wrote. `./install.sh --thumbnailer` also
removes definitions under the former name (`myos-md.thumbnailer`, `myos-markdown.thumbnailer`).

The older helper (`./installer/install-thumbnailer.sh install|check|uninstall`) writes the
same file but runs the system's `python3`: without the system's Pillow
(`python3-pil`) the previews stay empty.

## Frontmatter example

```markdown
---
background_color: "#ffe082"
note_style: "mitschrift"
---
# Einkauf
Milch
Zimt
Nudeln
```

## Notes

- Installer is idempotent: running it repeatedly is safe.
- Thumbnailer writes a tiny fallback PNG if Pillow is unavailable.
- Enable diagnostics via `SEITON_THUMBNAILER_DEBUG=1` (the former `MYOS_THUMBNAILER_DEBUG` is still read).
- Thumbnailers are asynchronous: previews may appear with a short delay.
