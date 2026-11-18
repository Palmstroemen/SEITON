"""Metadata helpers for PostFix markdown documents."""

import yaml

FRONTMATTER_BOUNDARY = "---"


class MetadataManager:
    """Handle YAML frontmatter parsing and updates for markdown text."""

    def split_frontmatter(self, text: str):
        """(the front matter as a dict, the body exactly as it is in text). Front matter that is
        no YAML mapping (broken, a list, a word) is no front matter: ({}, text), so nothing of
        it is lost when the note is saved."""
        lines = text.splitlines(keepends=True)
        if not lines or lines[0].strip() != FRONTMATTER_BOUNDARY:
            return {}, text
        for idx in range(1, len(lines)):
            if lines[idx].strip() == FRONTMATTER_BOUNDARY:
                yaml_text = "".join(lines[1:idx]).strip()
                body = "".join(lines[idx + 1:])
                try:
                    data = yaml.safe_load(yaml_text) if yaml_text else {}
                except yaml.YAMLError:
                    return {}, text
                if data is None:
                    data = {}
                if not isinstance(data, dict):
                    return {}, text
                return data, body
        return {}, text

    def build_frontmatter(self, meta: dict, body: str) -> str:
        """The note from its front matter and its body (unchanged: indentation at its start and
        its last line break stay). Comments in the YAML block are not kept: it is written anew."""
        yaml_text = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip() if meta else ""
        if yaml_text:
            return f"{FRONTMATTER_BOUNDARY}\n{yaml_text}\n{FRONTMATTER_BOUNDARY}\n{body}"
        return body

    def update_field(self, text: str, key: str, value) -> str:
        meta, body = self.split_frontmatter(text)
        meta[key] = value
        return self.build_frontmatter(meta, body)

    def get_field(self, text: str, key: str):
        meta, _ = self.split_frontmatter(text)
        return meta.get(key)
