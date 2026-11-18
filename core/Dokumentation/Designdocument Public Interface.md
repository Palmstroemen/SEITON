# Designdocument Public Interface

*Draft, 2026-11-18. Step 2 of "Kern und Apps trennen" in [docs/Roadmap.md](../../docs/Roadmap.md).*

## 1. Goal

Other people should be able to build apps for SEITON, and our own workshop apps are the first
examples of that: PostFix, SunTree, ClipboardTool. An app may use only what SEITON promises
publicly. What that promise covers is written down here and versioned. Everything else in
`core/`, `daemon/` and `cli/` may change at any time.

Rule: **the example apps use only the public interface.** A test checks it (section 6). This
way each example shows how a foreign app would do it. Once an app holds to the rule for a
while, it can move into a repository of its own (step 3 in the Roadmap).

Scope, Headline and Time are SEITON itself. They may keep using `core/` directly.

## 2. The four layers of the public interface

The outer a layer, the more stable and the more independent of Python it is. An app takes the
outermost layer that suffices.

| Layer | What | Who may use it |
|---|---|---|
| **1. Files** | `.seiton/` (Project.md, ACLs.md, Tags.md, Filters/, Trash/), the standard folders, `.TagsHere.json`, `seiton:` links | every program in every language, even without SEITON installed |
| **2. CLI** | `seiton ls`, `seiton project`, `seiton tag`, `seiton acl`, `seiton filter`, `seiton edit`, `seiton import`, `seiton export`, with `--json` where an app reads the output | every program that can start a process |
| **3. The daemon** | the perspective daemon's protocol (lens, shared place, clock) and the drive "Perspektiven" | programs that follow the lens or the place live |
| **4. Python** | a package `seiton` (section 4) | Python apps that want more than files and CLI |

ClipboardTool already lives on layer 1 alone: it writes a Markdown file into the project
folder and imports nothing of SEITON. That is the model for simple apps.

## 3. What the example apps use today

Measured on 2026-11-18 (imports outside the tests).

**SunTree**

| Today | For what | Public as |
|---|---|---|
| `core.scope_api.ScopeApi`: `list_entries`, `list_children`, `list_templates`, `create_folder`, `create_note`, `move_entry`, `move_entries`, `get_top_root`, `projects_root`, `get_effective_project_color`, `update_context` | the fan shows folders and embryos, drops into them | `seiton.places`, `seiton.entries`, `seiton.look` |
| `core.scope_api.start_place` | where to start | `seiton.places.start_place` |
| `core.perspective_drive.PROJECTS` | the name "Projekte" | `seiton.places.PROJECTS` |
| `core.settings.Settings`: `General/embryoOpacity`, `General/darkTheme`, its own group `SunTree` | look; its settings | `seiton.look` (General, read-only); the app's own group stays the app's own (see 5.3) |
| `core.color_schemes.load_scheme` | colours | `seiton.look.scheme()` |
| `daemon.lens_link.LensLink` | lens and shared place | `seiton.lens` |
| `Scope.window_icon.seiton_icon` | the SEITON icon | the files in `assets/brand/`; no import from Scope |
| `core.brand`: `getenv`, `NAME`, `file_name`, `legacy_file_names` | names | `seiton.brand` |

**PostFix**

| Today | For what | Public as |
|---|---|---|
| `core.acl_enforcement.allowed_at`, `core.identity.acl_user_for` | may the user write this note? | `seiton.rights.allowed(path, right)` |
| `core.acl_view.ACLView`, `RIGHTS_ORDER` | the rights panel shows who may what | `seiton.rights.view(path)` |
| `core.acl_edit`: `can_edit`, `own_rule`, `set_role_rights`, `set_user_roles`, `move_rules`, `check_move_rules`, the errors | editing rules; rules travel with a moved note | `seiton.rights` (edit functions and their errors) |
| `core.desk_service.DeskService.refresh_context` | the desktop follows the note's project | `seiton.context.focus(path)` |
| `core.project.notify_config_changed` | a changed `.seiton/` file takes effect | `seiton.context.config_changed(path)` |
| `core.brand`: `getenv`, `file_name`, `META_DIR`, `URL_SCHEME`, `LEGACY_URL_SCHEMES`, `env_name` | names, links | `seiton.brand` |
| `core.name_migration.take_over_old_config` | settings under the old name | not public: the migration is SEITON's job, not each app's (5.4) |
| `core.tag_chips` (was `Theme.tag_chips`) | tag colours | `seiton.look.tag_style()` |

**ClipboardTool:** nothing. Layer 1 only.

## 4. The package `seiton`

A thin layer over `core/`, at first without logic of its own: it only re-exports and names
things for the long term. A top-level package `seiton/` so it can later be installed as a
pip package of the same name.

```
seiton/
  __init__.py     API_VERSION = (0, 1)
  brand.py        NAME, META_DIR, URL_SCHEME, getenv, file_name
  places.py       PROJECTS, start_place, projects_root, top_root, project_of(path)
  entries.py      list_entries, list_children, templates, create_folder, create_note, move
  rights.py       allowed, view, can_edit, set_role_rights, set_user_roles, move_rules, errors
  look.py         scheme, project_color, embryo_opacity, dark, tag_style
  context.py      focus(path), config_changed(path)
  lens.py         Lens (today's LensLink)
```

Why apps must not use `os.rename` or `mkdir` directly for SEITON places: embryos are born on
first use, born empty folders turn back into embryos, rights and the trash are checked. `entries`
does this the same way Scope does.

## 5. Decisions to take

1. **Version promise.** `API_VERSION` as (major, minor): minor adds, major breaks. Until 1.0
   anything may change, but each change is noted in this document.
2. **Data rather than objects.** The public functions return plain values (str, Path, dict,
   lists), no `ScopeApi` objects. That keeps the internals free.
3. **Settings.** Each app keeps its own settings (decided 2026-11-18: own settings per
   program). SEITON publishes only the shared look (General) read-only. Open: does SunTree's
   tab on Scope's back stay, or does SunTree get its own settings window?
4. **Name migration.** One place for it, in SEITON's start, not in each app. Then PostFix no
   longer needs `core.name_migration`.
5. **Theme/.** Done with step 1 (2026-11-18): the tag styles moved to `core/` (`core.tag_chips`,
   `core.tag_styles`), the icons to `assets/icons/`; `seiton.look` is to re-export the styles.
6. **CLI with `--json`.** Which tools give machine-readable output first: probably `seiton ls` and
   `seiton project`.
7. **The daemon's protocol.** Today only `LensLink` knows it. To be documented with a version
   number before an app in another language may speak it.

## 6. The guard test

A test reads every Python file under the example apps with `ast` and collects its imports.
Allowed: the standard library, third-party packages, the app's own modules and `seiton`.
Forbidden: `core`, `daemon`, `cli`, `apps` (Scope, Headline, Time).

At first it starts with a list of today's exceptions (section 3) that may only shrink. Once
the list is empty, it is strict.

## 7. Order

1. Create `seiton/` as a pure facade, with tests that the facade gives the same as `core/`.
2. Guard test with today's exceptions.
3. SunTree to `seiton` (fewest uses), then PostFix. ClipboardTool already holds.
4. Decide 5.3 to 5.5 on the way.
5. The folders `apps/` and `examples/` (Roadmap step 1): done 2026-11-18.
