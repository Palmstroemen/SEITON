# **SEITON Filters & Perspectives - Design Document (Draft)**

## **1. Purpose**
The currently implemented system in SEITON is called **Filter**. Filters shape how data is shown without changing permissions and provide include/exclude/rule/group/flatten behavior.

The term **Perspective** names the flipped path-space navigation model, the lens (built since 2026-10-22, see section 14). It is intentionally not used for the filter runtime API.

---

## **2. Core Principles**
- **ACLs rule**: filters never reveal data beyond ACL permissions.
- **Flattened but traceable**: flattened views always know about origin and path and can show or use it on demand.
- **Self‑explanatory**: filter rules should be readable by non‑technical users.
- **Portable**: filters are stored as Markdown configs (`Filter.md`, in a folder or its `.seiton/`).

---

## **3. What a Filter Can Do**
- Include or exclude paths and folders (e.g., `/finanz/` with exceptions)
- Filter by filename patterns or extensions (e.g., `*.pdf`, `*rechnung*`)
- Filter by tags (future)
- Filter by AI analysis (future)
- Flatten deep trees while preserving provenance
- Group by project, folder, tag, or date (see section 8)
- Provide a custom UI profile (`Desk.md`)
- Name a lens (`## Perspective`; read, but it puts on nothing since 2026-10-26, see section 6)

---

## **4. Types of Filters**
### **4.1 Auto Filter**
Automatically applied when entering a folder context (e.g., CWD in `/finanz/`).

### **4.2 Manual Filter**
Explicitly selected by the user. Manual filters override auto filters.

Rule: The most specific explicit manual filter wins. If none is set, auto filter applies.

Built only in the CLI: `myfilter activate <file>` (or `--manual`) chooses one, and it acts on
what `myfilter resolve` and `myfilter show` report. Scope has no choice by hand: it was
taken back on 2026-10-26 ("Designdocument Perspective Resolver MVP.md", A6); in Scope only
auto filters act.

---

## **5. Persistence and Inheritance**
Filters are stored as Markdown files (`Filter.md`, `.seiton/Filter.md`, `.seiton/Filters/*.md`) and can exist in:
- project roots (inherited by subprojects)
- template roots (shared by template instances)
- normal folders in the tree or in templates (e.g., `/4_Finanz/` in the template for auto perspective)

A `Filter.md` (in the folder or its `.seiton/`) acts by itself. The collection in `.seiton/Filters/` is there to
choose from: it acts only when chosen by hand (`myfilter activate`, `--manual`; so only in `myfilter`, see 4.2),
so a file lying there cannot change a whole project unasked (2026-11-06).

Inheritance follows standard rules with `dynamic` as default. A future global mode `sparse` may store only deltas instead of full copies.

---

## **6. Filter Definition (Draft)**
Filters are defined with sections for scope, rules, and display. The parser accepts simple lines directly under headers and stops at empty lines, so the draft format below avoids blank lines inside sections.

Today rule lines contain no space: a line with a space ends its section, and the rules after it
are lost; for a space write `?` or `*` (`/Kunde?Huber/`). A filter whose `Name` contains a space
is skipped silently ("Prüfung 2026-11-18", B6). `Name` is required. `Scope` is read but does not
limit anything yet.

```
# Filter
Name: Finance
Scope: /4_Finanz/

## Include
/4_Finanz/
/5_Recht/

## Exclude
/4_Finanz/schwarzgeld/

## Filter
*/rechnung.pdf
*/invoice.pdf
*/*rechnung.*
*/*invoice.*
/*.jpg

## Flatten
true

## Group
project
tags

## Desk
Desk.md

## Perspective
4_Finanz/44_Rechnungen
```

`## Perspective` names a lens: a department and deeper levels, without a project (`..`
and `.` are refused). It was built (2026-10-25) to put the lens on when the filter was chosen
by hand. Since the choice by hand left Scope (2026-10-26) it is read and reported (`myfilter`,
ScopeApi's filter state, `lens`), but it puts on nothing. An auto filter never puts on a
lens ("Designdocument Perspective Resolver MVP.md", A6).

Open item: we may evolve the parser to allow more natural inline formatting later (e.g., `## Group_by: project`). We also keep “friendly input” options like pipe-separated lists (`| A | B | C`) in mind for the future, but not for MVP.

---

## **7. Flattening**
Flattening shows items in a single view while preserving origin:
- show source path as a badge or breadcrumb
- provide quick navigation back to original location

Flattening is a core USP for SEITON.
A limited form is the x-ray view (`core/xray.py`, Scope's X-ray button, on by default, and
`myls --roentgen`): small folders are seen through, smallest first and each completely or
not at all, while the listing fits without scrolling. Projects, empty, hidden and unreadable
folders stay folders. Files seen through carry the folder they lie in (Scope: a large, faint
folder behind the icon and a tooltip; myls: `(in Rechnungen/2024)`).

---

## **8. Grouping**
Grouping defines how views are organized:
- by project
- by folder segment
- by tag
- by date

Built: all four. `project` is the project each entry lies in (flattened across subprojects they
differ), `folder` its folder, `tag` its first tag, `date` the month it was last changed
(`2025-03`).

---

## **9. Security Considerations**
- filters never bypass ACLs
- hidden/system folders are excluded by default
- perspective rules are data, not executable scripts

---

## **10. Public API (Current)**
Public API currently lives in `core/perspective.py` and is used by CLI/GUI:
- `FilterConfig.from_file(path)`
- `FilterConfig.from_data(data)`
- `find_filters(start_path)`
- `resolve_active_filter(cwd, manual=None)`
- `resolve_effective_filter(cwd, manual=None, ...)` (with the chain of layers)
- `apply_filter_projection(entries, cwd=..., filter_state=...)`

Term note: **Perspective** is the lens; it has its own APIs (`core/perspective_session.py`, `core/perspective_drive.py`, the daemon), separate from the filters.

---

## **11. Open Questions**
- default storage location for global filters
- rule syntax for tags and AI filters

---

## **12. Not Realized Yet**
- tag‑based filters
- AI‑based filters
- `sparse` inheritance mode
- the choice by hand in Scope (section 4.2)

---

## **13. Summary**
Filters provide user‑friendly, powerful views over SEITON data:
- they filter and shape data without changing permissions
- they can flatten and group complex trees
- they are stored as portable Markdown configs

---

## **14. The Perspective (Lens)**
The flipped path-space Perspective (the lens) is described in a separate document:

- `core/Dokumentation/Designdocument Perspective Resolver MVP.md` (Part A: how the lens behaves for
  the user, decided 2026-10-22; Part B: the resolver contract)

This split keeps current Filter behavior stable while the lens has its own session and drive.
