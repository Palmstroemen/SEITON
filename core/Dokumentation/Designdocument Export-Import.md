# **SEITON Export/Import - Design Document (Draft)**

## **1. Purpose**
Define a portable export/import flow that:
- preserves project context and rules
- supports partial subtree exports
- allows safe re-import or adoption elsewhere

---

## **2. Scope**
**In scope (MVP):**
- export a subtree starting at a given path
- include project root config and ACLs
- include templates so a target system can continue working
- record reference path for re-import
- import with merge as default and explicit conflict modes

**Out of scope (MVP):**
- Live-SEITON bundle (optional later)
- OS-native ACL mapping
- advanced conflict UI

---

## **3. Terminology**
- **Project Root**: nearest folder containing `.seiton/Project.md`
- **Export Root**: the Project Root of the subtree being exported
- **Export Subtree**: the selected path under Export Root
- **Reference Path**: original absolute path of Export Root in source system
- **Package**: exported content as folder or zip archive

---

## **4. Export Modes**
### **4.1 Default: Folder**
The default export is a directory containing:
- the selected subtree
- `.seiton/` from Export Root (config, ACLs, templates reference)
- templates for the project
- export metadata
Default export name: `<ProjectName>_export_<YYYYMMDD>`.

### **4.2 Optional: Zip**
If `--zip` is set, the same content is packaged into a zip archive and the export folder is removed afterwards.

---

## **5. Export Contents**
### **5.1 Subtree**
Only real (physical) files and folders are exported. Embryos are not exported. The target can recreate them from templates.

### **5.2 Project Config**
Include `.seiton/` from Export Root (today the whole folder is copied, except its `Templates/`; see 5.3):
- `Project.md`
- `Templates.md`
- `Manifest.md` (if present)
- `Config.md` or equivalent single files
- `ACLs.md`

### **5.3 Templates**
Templates are always included so the receiver can continue working: the ones the project uses, in the package's `.seiton/Templates/` (where SEITON looks for them, so the package is a project with its templates). Optional future behavior: include templates read-only.

### **5.4 Metadata**
Export metadata records:
- source system identity (placeholder)
- export timestamp
- reference path for re-import
- export subtree path
Optional: a local export history log in the original project (for cloud binding or audit trails), e.g. `.seiton/ExportHistory.md` or a dedicated section in `Project.md`.

---

## **6. Reference Path**
The export stores the original location in `.seiton/Project.md` (a `# Export` block with `ReferencePath`, `Subtree`, `ExportedAt`, `Source`).

Example:
- Export subtree: `/Projekte/Haus/Dach/4_Finanz/44_Rechnungen/`
- Export Root: `/Projekte/Haus/Dach/`
- Reference Path: `/Projekte/Haus/Dach/`

---

## **7. Import Modes**
### **7.1 Restore Into Origin**
If the reference path exists, import attempts to reattach the subtree to its original location.

### **7.2 Adopt as New Project**
If reference path is absent or user chooses adoption, import creates or merges into a new target location.

---

## **8. Importer Design (MVP)**
### **8.1 Inputs**
- import source: folder or zip
- target base path (optional override)
- mode: restore or adopt
- conflict mode: merge, overwrite, skip, or per-file/per-folder decisions
- template handling: accept, ignore, or stage for review
- ACL handling: accept, ignore, or stage for review

Built today (`core/importer.py`, `cli/seiton_import.py`): source (folder or zip), `--target`, `--mode restore|adopt`, `--conflict merge|overwrite|skip`. Not built: per-file/per-folder decisions, template handling, ACL handling.

### **8.2 Steps**
Built today: 1, 2, 3, 5 and 7 (for the subtree only). Not built: 4, 6, 8, 9. The import copies only the subtree; the package's `.seiton/` (config, ACLs, templates) is not taken over.

1) Resolve package (unzip if needed into a temp directory)
2) Validate package structure (`.seiton/Project.md` exists)
3) Read export metadata from `Project.md` (`ReferencePath`, `Subtree`, `ExportedAt`, `Source`)
4) Run external virus scan (stub for MVP)
5) Resolve target root based on mode
6) Dry-run scan for conflicts and security checks
7) Apply selected conflict strategy
8) Apply ACL/template changes only if explicitly accepted
9) Write import summary report (optional)

### **8.3 Outputs**
- imported subtree placed at target location
- optional import report for conflicts and decisions

---

## **9. Conflict Strategy**
Default: **merge**.
Support conflict modes:
- merge (default)
- overwrite
- skip
- per-file/per-folder decision (interactive or batch rule)

Built: `merge` keeps an existing file and adds the new ones; `overwrite` replaces existing files. `skip` is accepted but does the same as `merge` today (`core/importer.py`, `_copy_tree_secure`). Per-file/per-folder decisions are not built.

---

## **10. ACL and Template Deltas**
Template or ACL changes from the export have to be made **visible** and can be explicitly accepted or ignored.
Use case: team lead reviews ACLs prepared by another person.

---

## **11. Source Identity**
Record a source identifier for provenance and collaboration.
Options (non-binding):
- hostname + user
- MAC address
- generated project UUID

Built today: `user@hostname` (`Source:` in the export block).

---

## **12. Security Considerations**
- do not export hidden/system folders outside the subtree (not held yet: the export copies the project's whole `.seiton/`, its `Trash/` and `audit.log` too; "Prüfung 2026-11-18", D1)
- keep ACLs as data, do not apply OS ACLs during import
- validate paths to prevent traversal during import

---

## **13. Public API**
Public API lives in `core/exporter.py` and `core/importer.py`; the CLI uses it (`cli/seiton_export.py`, `cli/seiton_import.py`), the GUI does not yet:
- `export_subtree(source_path, output_dir, package_name=None, zip_output=False)`
- `import_package(package_path, target_root=None, mode="adopt", conflict="merge")`

---

## **14. Open Questions**
- live SEITON bundle as optional export target?
- read-only template export mode?
- conflict resolution UI for large imports?
- path length constraints and project "splitting" support?

---

## **15. Not Realized Yet**
- Importer: conflict UI and per-file/per-folder decisions; a `skip` of its own (today the same as `merge`)
- Importer: showing and accepting ACL and template changes (section 10); the package's `.seiton/` is not taken over
- Importer: virus scan, dry run, import report
- Export history log in the original project
- Live-MyOS bundle option
- Read-only template export option
- Path splitting for very long paths

---

## **16. Summary**
The export/import design aims for portability and clarity:
- subtree exports rooted in a project
- config and ACLs always travel with the data
- templates included to keep SEITON functional
- reference path enables re-import into the original location
