# **SEITON Markdown Parser - Design Document (Draft)**

## **1. Purpose**
Define the parsing rules for SEITON Markdown configuration files (in `.seiton/`; code: `core/config/parser.py`, `MarkdownConfigParser`) to keep them human-friendly, consistent, and machine-readable.

---

## **2. Core Rules (MVP)**
- Sections start with headers (`#`, `##`, `###`).
- Lines directly under a header are interpreted as list items.
- Empty lines end the current section.
- Key-value pairs use `Key: Value`.
- Comma-separated values are split into list entries.
- Lines with multiple words are treated as prose and end the section.
- Repeated headers merge their items.
- A list item may start with `* ` and then contain spaces (`* Standard Plus`); `- ` is not
  a list item here and ends the section.
- `#` after a value starts an inline comment.
- A header needs a space after the hashes (`#tag` is no header).
- A header line with `key: value` (`#### inherit: dynamic`) is a property of the current
  section, not a new section.
- Values of `Key: Value` come back as lists (`Version: 1.0` → `{Version: [1.0]}`).

---

## **3. Examples**
### **3.1 Simple List**
```
# Templates
Standard
Person
```

### **3.2 Comma List**
```
# Templates
Standard, Person, FiBu
```

### **3.3 Key-Value**
```
# Project
Version: 1.0
Owner: Oliver
```

### **3.4 Repeated Header (Merge)**
```
# Templates
Standard
Person

# Notes
This comment ends the list.

### Templates
FiBu
Scrum
```

Result: `Templates = [Standard, Person, FiBu, Scrum]`

---

## **4. What Ends a Section**
- An empty line
- A line with multiple words (prose)
- A non-parseable line

---

### **4.1 Files with rules of their own**
`ACLs.md` and `Desk.md` do not follow 4: blank lines, notes and `<!-- comments -->` do not end
a section there (see "Designdocument ACLs.md", 2.3, and "Designdocument Desk.md", 5).
`Tags.md` and the folder tags (`myTags.md`) are not read with this parser at all (see
"Designdocument Tags.md", 3).

---

## **5. Friendly Input (Future)**
Potential future extensions that are not part of the MVP:
- Pipe-separated lists (e.g., `| Standard | Person | FiBu`)
- Inline grouping syntax (e.g., `## Group_by: project`)
- More flexible paragraph handling

---

## **6. Notes**
The parser is intentionally strict to avoid ambiguity. The goal is “write it naturally, but still predictably.”
