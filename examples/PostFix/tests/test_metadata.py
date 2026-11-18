"""The front matter of a note (examples/PostFix/metadata.py): opening and saving keeps the note's text as
it is ("docs/Prüfung 2026-11-18.md", PF6, PF7) - only the YAML block is written anew."""

from examples.PostFix.metadata import MetadataManager

M = MetadataManager()


def test_the_body_stays_as_it_is():
    for text in ("---\na: 1\n---\n    eingerückter Code\n",
                 "---\na: 1\n---\n\n# Titel\n\nText.\n",
                 "---\na: 1\n---\n# Titel ohne Leerzeile\n",
                 "---\na: 1\n---\nohne letzte Zeilenschaltung"):
        meta, body = M.split_frontmatter(text)
        assert meta == {"a": 1}
        assert M.build_frontmatter(meta, body) == text, repr(text)


def test_a_note_without_front_matter_stays():
    for text in ("# Titel\n\nText.\n", "    code\n", ""):
        meta, body = M.split_frontmatter(text)
        assert meta == {} and body == text
        assert M.build_frontmatter(meta, body) == text


def test_broken_front_matter_is_kept_as_text():
    for text in ("---\na: [kaputt\n---\nText\n", "---\n- eine\n- Liste\n---\nText\n", "---\nnur ein Wort\n---\nText\n"):
        meta, body = M.split_frontmatter(text)
        assert meta == {} and body == text, repr(text)
        assert M.build_frontmatter(meta, body) == text
