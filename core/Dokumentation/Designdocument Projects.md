# **SEITON Projects Configuration System - Redesign**

## **1. Core Philosophy**
**"Convention over Configuration"** - Like Git, SEITON uses a simple hidden directory (`.seiton/`, until November 2026 `.MyOS/`) with human-readable Markdown files. No complex manifests, no duplicate bookkeeping.

## **2. Project Definition**
A **SEITON Project** is any directory containing a `.seiton/` directory **and** a marker file `.seiton/Project.md`. Inside `.seiton/`, Markdown (`.md`) files are loaded as configuration according to the parser rules.

## **3. Directory Structure**
```
project/
├── .seiton/                  # SEITON configuration directory
│   ├── Project.md            # Required marker file
│   ├── .created.json         # What creating the project wrote (see 5.1)
│   ├── Templates.md          # Template configuration (optional)
│   ├── Manifest.md           # Project metadata (optional)
│   ├── Config.md             # Inheritance rules (optional)
│   ├── ACLs.md               # Access lists (optional)
│   └── any-other.md          # Custom configuration files
├── documents/                # User data
├── images/
└── .git/                     # Optional: Git repository
```

## **4. File Formats (All Markdown)**

### **4.1 Templates.md (Recommended)**
```markdown
# Templates
Standard
Person
Finanzen
```

**Parsing:** Plain lines under `# Templates` are template names.

### **4.2 Manifest.md (Optional)**
```markdown
# Project
Version: SEITON v0.1
Owner: Anna
Created: 2025-01-27
Status: Active
Priority: High
```

**Parsing:** Key-value pairs (`Key: Value`) are parsed. Unknown keys are kept as metadata.

### **4.3 Other .md files**
Any `.md` file in `.seiton/` is loaded and parsed with the MarkdownConfigParser.  
Sections are defined by `# Section` headers; values are key-value pairs (`key: value`) or lists.

**Two configuration styles (can be mixed):**
1. **Single files** (e.g. `Templates.md`, `Manifest.md`, `ACLs.md`)
2. **A single `Config.md`** with multiple `# Section` blocks

**Equivalence rule:**  
A section in `Config.md` that starts with `# Templates` is equivalent to a file named `Templates.md` with the same content.  
Built for the sections `ProjectConfig` resolves (today `Templates`). `ACLs.md`, `Tags.md` and
`Desk.md` are read only as their own files.

## **5. Configuration Loading Algorithm (Verbally)**

### **5.1 `ProjectConfig` Class (`core/project.py`)**
`ProjectConfig` encapsulates loading and writing project configuration from `.seiton/`.

- **`is_valid()`**  
  Checks whether `.seiton/Project.md` exists (marker file).

- **`load()`**  
  Loads local `.seiton/` files and resolves effective template config at runtime
  via nearest-ancestor lookup.

- **`_load_from_settings_dir()`**  
  Loads individual files:
  - `Templates.md` → `templates`
  - `Manifest.md` → `metadata` + `version`
  - `Config.md` → `config_data`

- **`get_inherit_status(section)`**  
  Reads the `inherit` rule for a section; default is `dynamic`.

- **`create(path)`**  
  Turns a folder into a project (Scope's P-Button via `make_project`, `myproject create`):  
  1) Finds a parent with `.seiton/` (else refuses)  
  2) Writes `.seiton/Project.md` (`# SEITON Project`) in the new folder  
  3) Copies the files of the templates' root `.seiton` (`ACLs.md`, `Desk.md`, …) into it,
     without overwriting (`core/template_seed.py`, see "Designdocument ACLs.md", 10)  
  4) Records what it wrote in `.seiton/.created.json` (`core/project_unmake.py`)  
  5) Leaves section inheritance to resolve-on-read: the parent's config files are not copied

- **Turning a project back** (`core/project_unmake.py`, the crossed-out P-Button)  
  Removes `.seiton` when nothing of the project's own came since creating it (by
  `.created.json`); otherwise only after asking, and then `.seiton` goes into the parent
  project's trash as "SEITON settings". Not for the top project; subprojects stay projects.
  Separate from this, `myproject tidy` turns unused born template folders back into embryos
  (see "Designdocument BlueprintLayer.md", 3.2).

- **`propagate_config(section, dry_run)`**  
  Materializes a section into child projects when explicitly requested.

- **`find_config_in_parents(start_path, config_name)`**  
  Generic file resolver for `/.seiton/<config_name>` using nearest-ancestor lookup.

**Override + Inheritance rules (resolve-on-read):**
- **Single files override `Config.md`** for the same section.
- **Nearest ancestor wins** for missing local sections.
- **Inheritance can be defined in both** single files and `Config.md` sections.
- If a section has **no inherit defined**, the default is **`dynamic`** (keep searching up).
- API policy: prefer **parameterized generic commands** over file-specific methods.

### **5.2 Markdown Parser (`core/config/parser.py`)**
The parser reads `# Section` blocks and converts lines into simple data structures
(key-value pairs, lists), so `ProjectConfig` can extract `inherit`, `items`, and similar fields.

## **6. Template Merging Logic**
The template system combines multiple template folders into a single **embryo tree**:
1. Scan each template directory (folders only, ignore hidden items).
2. Folder names are embryo names as they are (no `%` suffix).
3. Deep‑merge all template trees into one combined structure.
4. Missing templates are skipped with a warning.

## **7. FUSE Integration**
The FUSE blueprint layer:
- Validates the project with `ProjectConfig.is_valid()`.
- Reads effective templates from `ProjectConfig.get_effective_templates()` and builds the embryo tree.
- Exposes the merged structure as a virtual filesystem view.
- Shows and births embryos by the ACLs only with `SEITON_ACL_MODE=enforce` (see
  "Designdocument BlueprintLayer.md", 7).

## **8. CLI Commands**
Built (`cli/myproject.py`):
- `myproject create <path> [--new]`: create a project
- `myproject tidy [path]`: turn unused born template folders back into embryos
- `myproject trash …`: the project's trash (see "Designdocument Trash.md")

Planned:
- Add/remove templates
- Show project status and templates
- Edit config and show inheritance chain
- Propagate config/template changes to subprojects (the core has `propagate_config`, no CLI)

## **9. Testing Strategy**

### **9.1 Test Structure**
```
test_lab/
├── .seiton/
│   └── Templates.md      # Global: Standard
└── plate/
    ├── .seiton/
    │   └── Templates.md  # All projects: Standard
    ├── Haus/
    │   ├── .seiton/
    │   │   └── Templates.md  # Standard, Person
    │   └── Dach/
    │       ├── .seiton/
    │       │   └── Templates.md  # Standard, Person, Finanzen
    │       └── Webseite/
    │           └── .seiton/
    │               └── Templates.md  # Standard
    └── Garten/
        └── .seiton/
            └── Templates.md  # Person
```

### **9.2 Key Test Cases**
1. **Empty .seiton/** with `Project.md` - Valid project
2. **Missing Templates.md** - Templates list is empty
3. **Missing local Templates.md** - Inherits nearest ancestor templates at runtime
4. **inherit:not** - Stops runtime inheritance for that section
5. **propagate_config(dry_run)** - Reports materialization targets
6. **Malformed Markdown** - Parser falls back safely

## **10. Error Handling & Validation**

### **10.1 Graceful Degradation**
- Missing `.seiton/` or `.seiton/Project.md` → Clear error message
- Missing template → Warning log, skip that template
- Invalid Markdown → Fallback to default parsing

### **10.2 Validation**
- Template names must exist in the templates directory (the nearest `.seiton/Templates` upwards, see "Designdocument BlueprintLayer" 2.3); a missing one is skipped with a warning
- Check for Markdown syntax errors (basic) (not checked whether built)
- Detect circular inheritance in hierarchy (not built: inheritance follows the folder tree, which has no cycles)

## **11. Migration Path**

### **11.1 From Old System**
Historical (the `.project.cfg` system is gone; its code lies in `core/archive/`):
```python
# Old: .project.cfg
# New: .MyOS/Templates.md (today .seiton/Templates.md)

# Migration script:
def migrate_old_project(project_path):
    old_cfg = project_path / ".project.cfg"
    new_dir = project_path / ".MyOS"
    
    if old_cfg.exists():
        new_dir.mkdir(exist_ok=True)
        content = old_cfg.read_text()
        # Convert to Templates.md format
        new_content = convert_to_markdown(content)
        (new_dir / "Templates.md").write_text(new_content)
        old_cfg.unlink()
```

### **11.2 From MyOS to SEITON (2026-11-14)**
`python3 cli/migrate_name.py` (`core/name_migration.py`) moves `.MyOS/` to `.seiton/`,
`~/.config/MyOS` to `~/.config/seiton` and the xattrs `user.myos.*` to `user.seiton.*`.
Nothing of it runs by itself at start. A `Project.md` with the old heading `# MyOS Project`
still marks an unchanged project.

---

## **Implementation Priority**

1. **Phase 1**: New `ProjectConfig` class with `.MyOS/` (today `.seiton/`) detection
2. **Phase 2**: Markdown parser for configuration files
3. **Phase 3**: Template inheritance and merging
4. **Phase 4**: Update Blueprint to use new system
5. **Phase 5**: Update all tests
6. **Phase 6**: CLI tools for project management

This design provides a **simple, extensible, and intuitive** configuration system that follows Unix/Git conventions while maintaining SEITON's human-readable philosophy.
