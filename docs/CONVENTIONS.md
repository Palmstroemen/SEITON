# Documentation Conventions

## Language

- **English:** Technical documentation (README, API docs, tests, setup guides)
- **German:** Internal/operational docs (ProjectLogbook, docs/Vision, some design notes) — acceptable for contributor-facing docs that stay in-repo

## Naming

- **README:** Always `README.md` (uppercase)
- **Design documents:** `Designdocument X.md` in `core/Dokumentation/`; entry point: `docs/Designdokument.md`
- **Status docs:** `STATUS.md`, `SECURITY.md` in `docs/`

## Frontmatter

PostFix/Scope-style YAML frontmatter (window size, colors, etc.) is optional. Use only where the document is opened in PostFix and needs layout hints. Omit for plain reference docs.

## Code

- Code comments are in English.
- Security-relevant blocks get a header comment that begins with the keyword, e.g.
  `# Security: To avoid ...`.
- Never write code you cannot see or fully understand in this repository.
