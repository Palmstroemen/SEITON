# **SEITON Blueprint Layer - Design Document**

## **1. Overview**
The `Blueprint` class implements a **FUSE (Filesystem in Userspace)** layer that overlays virtual
"embryo folders" (no `%` suffix) on top of real directories. These virtual folders become real
("born") on first write access.

The same class is also used without FUSE: Scope (`core/scope_api.py`), the perspective
session and the cloud embryos (`core/cloud_embryos.py`) ask it for embryos and births.

## **2. Core Architecture**

### **2.1 Embryo Concept**
- **Embryo Folder**: Virtual directory shown with its **plain name** (e.g., `0_Admin`)
- **Birth**: Automatic creation of a real directory when accessed for writing
- **Template-based**: Embryo structure defined by template directories
- **Reabsorb**: A born folder that holds nothing of the user (only unchanged copies of its
  template) can become an embryo again (`reabsorb_upwards`, `reabsorb_all`)

### **2.2 Project Detection**
A project is valid if `.seiton/Project.md` exists. `ProjectConfig` loads templates from
`.seiton/Templates.md` (or a `# Templates` section in `.seiton/Config.md`); a project without
its own inherits them from the nearest parent project (`get_effective_templates()`).

### **2.3 Template Sources**
Templates are loaded from (`core/template_place.py`):
- `SEITON_TEMPLATES_DIR` (if set; the former `MYOS_TEMPLATES_DIR` is still read), otherwise
- the nearest `.seiton/Templates` from the project upwards: `<project_root>/.seiton/Templates`,
  else a parent folder's (e.g. `~/.seiton/Templates`). The nearest one wins as a whole (no merging by name). A plain
  `Templates/` folder is never taken (`~/Templates`, a cloud's own `Templates` folder).

## **3. Blueprint Responsibilities**

### **3.1 Initialization**
`Blueprint.__init__()`:
1. Finds the project root by searching for `.seiton/Project.md`
2. Loads `ProjectConfig` for that project
3. Reads template names from `ProjectConfig.get_effective_templates()`
4. Builds the embryo tree from all templates
5. Initializes `BirthClinic` for safe materialization
6. Loads the project's ACL policy and the user's roles (`core.identity`)

### **3.2 Birth Process**
When a path contains embryos, `BirthClinic.give_birth()`:
- Finds the template source for the embryo path
- Validates template safety (no symlinks)
- Copies the template into the project (without symlinks), including the template
  folder's own `.seiton`

`BirthClinic.reabsorb()` is the reverse: it removes a born folder only when it holds nothing
but unchanged copies of its template. Scope calls it after an operation emptied a folder
(`reabsorb_upwards`); `seiton project tidy` does it for the whole project (`reabsorb_all`).

## **4. Embryo Tree Structure**
The embryo tree is a nested dictionary of folder names:

```
.seiton/Templates/Standard/
├── 0_Admin/
├── 1_Info/
└── 3_Kommunikation/
    ├── 31_Intern/
    └── 35_Kunden/

Embryo tree:
{
  "0_Admin": {},
  "1_Info": {},
  "3_Kommunikation": {
    "31_Intern": {},
    "35_Kunden": {}
  }
}
```
(Shortened from `templates/Standard`.) Hidden folders of a template (its `.seiton`) are no
embryos.

## **5. Security Measures**
- Block path traversal (`..`) in embryo paths
- Block absolute and hidden paths
- Validate template names before using them
- Reject symlinks inside template directories
- Copy templates without following symlinks
- Warn when symlinks exist in the project path

## **6. FUSE Operations (Summary)**
- **`getattr()`**: Returns real attributes or read‑only attributes for embryos
- **`readdir()`**: Lists physical entries first (hidden ones left out), then embryos not yet
  born, then the virtual level folders of a sorted folder (see "Designdocument Sort.md")
- **`mkdir()` / `create()`**: Triggers birth if embryos appear in the path
- **`write()` / `release()`**: Delegate to OS file operations

## **7. Permission System**
`_can_write_embryo()` decides whether an embryo is shown and may be born. It follows the ACL
mode like the rest of SEITON: with `SEITON_ACL_MODE` off (the default) or `monitor`, or
without an `ACLs.md`, every embryo is shown. Only with `enforce` an embryo needs `write` for
one of the user's roles; a user without roles then sees none. `get_embryos_at()` already
filters with it.

`_has_write_permission_for_embryo()` in `readdir()` is a leftover placeholder (returns
`True`); it has no effect, since the names it sees are already filtered.

## **8. Mount Interface**
`Blueprint.mount(project_path, foreground=True)` mounts FUSE on the project root.

CLI usage:
```bash
python localBlueprintLayer.py /path/to/project
```

## **9. Testing Considerations**
Key scenarios:
1. Embryos are shown virtually before birth
2. Birth happens on first write
3. Template trees merge correctly
4. Path traversal is blocked
5. Symlinks in templates are rejected

## **10. Limitations / Next Steps**
- Template merging is currently simple (deep merge)
- Logging could replace some `print()` statements in the future
- `Blueprint.DEFAULT_TEMPLATES_DIR` (`~/.myos/templates`) is an unused leftover; the templates
  come from `core/template_place.py` (2.3)