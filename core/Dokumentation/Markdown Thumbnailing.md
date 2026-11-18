# SEITON Markdown Thumbnailing (Linux)

## Goal

Show attractive previews for `*.md` files in common Linux file browsers (Nautilus, Dolphin, Nemo, Thunar where supported) using the Freedesktop thumbnail standard, without changing Markdown file content.

## Architecture

- **Renderer:** `core/thumbnailer/markdown_thumbnailer.py`
- **CLI entrypoint:** `scripts/seiton_md_thumbnailer.py`
- **Thumbnailer registration:** `installer/seiton-md.thumbnailer` (a template; the installer fills in the paths)
- **Installer integration:** `./install.sh --thumbnailer` (`installer/seiton_install.py`, `thumbnailer()`)

Not used by any installer: `core/bin/seiton-md-thumbnailer` and
`installer/thumbnailers/seiton-markdown.thumbnailer` (it points to `/usr/local/bin`, where
nothing links the CLI). Leftovers from an earlier way ("Prüfung 2026-11-18", D11).

## Freedesktop Integration

`seiton-md.thumbnailer` declares:
- MIME types: `text/markdown`, `text/x-markdown`
- command contract: `%i` input path, `%o` output png, `%s` requested size

Installed user-local to:
- `~/.local/share/thumbnailers/seiton-md.thumbnailer`

`./install.sh --thumbnailer` writes it with the venv's Python and the repo path, and lists it
for `./install.sh --uninstall`. Definitions under the former name (`myos-md.thumbnailer`,
`myos-markdown.thumbnailer`) are not removed by it yet ("Prüfung 2026-11-18", D10); the
older helper `installer/install-thumbnailer.sh` does remove them.

## Rendering Rules

- square PNG output (`size x size`)
- note style: from `note_style` in the frontmatter, else detected (files in `.seiton`: config
  card; a long chat: speech bubble; fewer than 10 lines: Post-it; fewer than 100: A4 sheet;
  else notebook). The styles and their names: `installer/thumbnailer.md`.
- background color from markdown:
  - first `background_color: #hex` in YAML frontmatter
  - fallback: first body line matching same key
  - default: depends on the style (Post-it `#fff59d`)
- subtle border per style (Post-it: a folded corner) for the "note" look
- readable snippet (first meaningful lines, markdown syntax stripped)

## Security Rules

- remove script tags (`<script>...</script>`)
- strip HTML tags from preview text
- strip control characters
- markdown links render as text label only (`[label](url)` -> `label`)
- ignore executable URL schemes in preview context (`javascript:`, `data:text/html`)
- no execution of markdown/HTML/javascript during thumbnailing

## Performance Rules

- no network access
- no external process execution
- bounded output size (`64..1024`)
- small in-memory operations only

## Rollout (Suggested)

1. Enable current Linux thumbnailer flow (done in this phase).
2. Add optional cache invalidation helper for development/debugging.
3. Expand metadata support (e.g., project tint fallback from `.seiton` context).
4. Add non-Linux adapters later (Windows preview handlers, macOS QuickLook plugin).
