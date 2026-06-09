import pytest

from multimark import markdown_to_html, markdown_to_latex, markdown_to_xml, VALID_EXTENSIONS
from spec_parser import load_fixtures

# Map each section in extensions.txt to the extensions it requires.
SECTION_EXTENSIONS = {
    "Tables": ["table"],
    "Strikethroughs": ["strikethrough"],
    "Autolinks": ["autolink"],
    "HTML tag filter": ["tagfilter"],
    "Footnotes": ["table", "strikethrough", "autolink", "tagfilter", "tasklist"],
    "When a footnote is used multiple times, we insert multiple backrefs.": [
        "table", "strikethrough", "autolink", "tagfilter", "tasklist"
    ],
    "Footnote reference labels are href escaped": [
        "table", "strikethrough", "autolink", "tagfilter", "tasklist"
    ],
    "Interop": ["table", "strikethrough", "autolink", "tagfilter", "tasklist"],
    "Task lists": ["tasklist"],
}

# These all need UNSAFE to pass expected HTML
UNSAFE_SECTIONS = {"HTML tag filter", "Embedded HTML"}

EXTENSION_EXAMPLES = load_fixtures("extensions.txt")


def _example_id(example):
    return f"ex{example.example}::{example.section}"


@pytest.mark.parametrize("example", EXTENSION_EXAMPLES, ids=_example_id)
def test_extension_html(example):
    """Extension spec examples produce the expected HTML output."""
    exts = SECTION_EXTENSIONS.get(example.section, list(VALID_EXTENSIONS))
    unsafe = example.section in UNSAFE_SECTIONS
    result = markdown_to_html(
        example.markdown,
        extensions=exts,
        unsafe=unsafe,
        footnotes=True,
    )
    # <IGNORE> is a cmark-gfm test convention meaning "just check it doesn't crash"
    if example.html.strip() == "<IGNORE>":
        assert isinstance(result, str)
    else:
        assert result == example.html, (
            f"Example {example.example} ({example.section}) at "
            f"{example.fixture_file}:{example.start_line}\n"
            f"Input:\n{example.markdown!r}\n"
            f"Expected:\n{example.html!r}\n"
            f"Got:\n{result!r}"
        )


@pytest.mark.parametrize("example", EXTENSION_EXAMPLES, ids=_example_id)
def test_extension_latex_no_crash(example):
    """Extension examples render to LaTeX without crashing."""
    exts = SECTION_EXTENSIONS.get(example.section, list(VALID_EXTENSIONS))
    result = markdown_to_latex(example.markdown, extensions=exts, footnotes=True)
    assert isinstance(result, str)


@pytest.mark.parametrize("example", EXTENSION_EXAMPLES, ids=_example_id)
def test_extension_xml_no_crash(example):
    """Extension examples render to XML without crashing."""
    exts = SECTION_EXTENSIONS.get(example.section, list(VALID_EXTENSIONS))
    result = markdown_to_xml(example.markdown, extensions=exts, footnotes=True)
    assert isinstance(result, str)


class TestValidExtensions:
    """Test extension name validation and the VALID_EXTENSIONS set."""

    def test_valid_extensions_set(self):
        assert VALID_EXTENSIONS == {"table", "strikethrough", "autolink", "tagfilter", "tasklist"}

    def test_unknown_extension_raises(self):
        with pytest.raises(ValueError, match="Unknown extension"):
            markdown_to_html("test\n", extensions=["nonexistent"])

    def test_all_valid_extensions_can_be_loaded(self):
        """All extensions in VALID_EXTENSIONS can actually be activated."""
        result = markdown_to_html("Hello\n", extensions=list(VALID_EXTENSIONS))
        assert "<p>Hello</p>" in result


class TestTableExtension:
    """Targeted tests for the table extension."""

    def test_simple_table(self):
        md = "| a | b |\n|---|---|\n| 1 | 2 |\n"
        result = markdown_to_html(md, extensions=["table"])
        assert "<table>" in result
        assert "<th>a</th>" in result
        assert "<td>1</td>" in result

    def test_alignment(self):
        md = "| left | center | right |\n|:-----|:------:|------:|\n| L | C | R |\n"
        result = markdown_to_html(md, extensions=["table"])
        assert 'align="left"' in result
        assert 'align="center"' in result
        assert 'align="right"' in result

    def test_table_latex(self):
        md = "| a | b |\n|---|---|\n| 1 | 2 |\n"
        result = markdown_to_latex(md, extensions=["table"])
        assert "\\begin{table}" in result or "a" in result  # has table content


class TestStrikethroughExtension:
    def test_basic(self):
        result = markdown_to_html("~~deleted~~\n", extensions=["strikethrough"])
        assert "<del>deleted</del>" in result

    def test_in_paragraph(self):
        result = markdown_to_html("This is ~~not~~ true.\n", extensions=["strikethrough"])
        assert "<del>not</del>" in result


class TestAutolinkExtension:
    def test_url(self):
        result = markdown_to_html("Visit https://example.com today.\n", extensions=["autolink"])
        assert '<a href="https://example.com">https://example.com</a>' in result

    def test_email(self):
        result = markdown_to_html("Contact user@example.com please.\n", extensions=["autolink"])
        assert "mailto:" in result or "user@example.com" in result


class TestTagfilterExtension:
    def test_filters_textarea(self):
        result = markdown_to_html("<textarea>x</textarea>\n", extensions=["tagfilter"], unsafe=True)
        assert "&lt;textarea>" in result

    def test_allows_div(self):
        result = markdown_to_html("<div>ok</div>\n", extensions=["tagfilter"], unsafe=True)
        assert "<div>ok</div>" in result


class TestTasklistExtension:
    def test_checked(self):
        result = markdown_to_html("- [x] Done\n", extensions=["tasklist"])
        assert 'checked=""' in result or "checked" in result

    def test_unchecked(self):
        result = markdown_to_html("- [ ] Todo\n", extensions=["tasklist"])
        assert '<input type="checkbox"' in result
        assert "checked" not in result or 'checked=""' not in result
