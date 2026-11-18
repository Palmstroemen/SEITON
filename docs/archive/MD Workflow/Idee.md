> Archived 2026-11-18 – an idea from February 2026 (Markdown first, exports to Office, Dolphin actions, an Obsidian plugin); nothing of it is used today.

Vorteile dieses Systems:
MD-first: Gedanken zuerst in Markdown

Tag-Propagation: Tags fließen in Office-Dokumente

Nachvollziehbarkeit: Export-Historie wird protokolliert

Flexibel: CLI, GUI, Obsidian-Integration

Einfach: _folder.tags.md ist leicht verständlich

📁 Projekt/
├── 📄 konzept.md                    # MD-Quelldatei
├── 📄 konzept.md.actions.yaml       # Aktionen/Tags
├── 📄 konzept.pdf                   # Generiertes PDF
├── 📄 konzept.pptx                  # Generierte Präsentation
└── 📁 .md-workflow/                 # Workflow-Metadaten
    ├── 📄 konzept.exports.json      # Export-Historie
    └── 📄 tags-cache.json           # Tag-Index