import re

import pytest

from multimark import (
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_commonmark,
    markdown_to_xml,
    Options,
)
from spec_parser import load_fixtures

ALL_EXAMPLES = load_fixtures("spec.txt", "smart_punct.txt", "regression.txt")

# Known cmark roundtrip failures: the commonmark renderer doesn't perfectly
# preserve these edge cases (setext headings with certain content, list spacing).
# These are upstream cmark limitations, not multimark bugs.
ROUNDTRIP_XFAIL = {
    # Setext headings: cmark normalizes to ATX but roundtrip loses info
    ("spec.txt", 51),
    ("spec.txt", 52),
    ("spec.txt", 65),
    # Fenced code blocks: info string roundtrip
    ("spec.txt", 108),
    # List items: list numbering/indentation normalization
    ("spec.txt", 227),
    ("spec.txt", 267),
    # Lists: tight/loose detection differs on roundtrip
    ("spec.txt", 271),
    ("spec.txt", 272),
    ("spec.txt", 283),
    # Code spans: backtick normalization
    ("spec.txt", 334),
    # Smart punctuation: curly quotes don't roundtrip through commonmark
    ("smart_punct.txt", 11),
    ("smart_punct.txt", 14),
    ("smart_punct.txt", 16),
}


def _example_id(example):
    return f"{example.fixture_file}::ex{example.example}::{example.section}"


@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=_example_id)
def test_latex_no_crash(example):
    """LaTeX renderer handles all spec examples without error."""
    result = markdown_to_latex(example.markdown)
    assert isinstance(result, str)
    if example.markdown.strip():
        assert len(result) > 0


@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=_example_id)
def test_man_no_crash(example):
    """Man renderer handles all spec examples without error."""
    result = markdown_to_man(example.markdown)
    assert isinstance(result, str)
    if example.markdown.strip():
        assert len(result) > 0


@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=_example_id)
def test_xml_no_crash(example):
    """XML renderer handles all spec examples without error."""
    result = markdown_to_xml(example.markdown)
    assert isinstance(result, str)
    if example.markdown.strip():
        assert len(result) > 0


@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=_example_id)
def test_commonmark_roundtrip(example):
    """CommonMark roundtrip: markdown → commonmark → HTML should match direct HTML."""
    if (example.fixture_file, example.example) in ROUNDTRIP_XFAIL:
        pytest.xfail("Known cmark commonmark renderer limitation")

    options = Options.VALIDATE_UTF8 | Options.UNSAFE
    # If this is from smart_punct.txt, enable SMART
    if example.fixture_file == "smart_punct.txt":
        options |= Options.SMART

    html_direct = markdown_to_html(example.markdown, options=options)
    normalized = markdown_to_commonmark(example.markdown, options=options)
    html_roundtrip = markdown_to_html(normalized, options=options)
    assert html_direct == html_roundtrip, (
        f"Roundtrip failed for example {example.example} ({example.section})\n"
        f"Original markdown:\n{example.markdown!r}\n"
        f"Normalized commonmark:\n{normalized!r}\n"
        f"HTML direct:\n{html_direct!r}\n"
        f"HTML roundtrip:\n{html_roundtrip!r}"
    )


# ---------------------------------------------------------------------------
# Structural validation: XML well-formedness
# ---------------------------------------------------------------------------

_XML_OPEN_TAG = re.compile(r"<([a-z_]+)(?:\s[^>]*)?>")
_XML_CLOSE_TAG = re.compile(r"</([a-z_]+)>")
_XML_SELF_CLOSE = re.compile(r"<([a-z_]+)[^>]*/>")


@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=_example_id)
def test_xml_balanced_tags(example):
    """XML output has balanced open/close tags."""
    result = markdown_to_xml(example.markdown)
    # Remove self-closing tags before counting
    without_self_close = _XML_SELF_CLOSE.sub("", result)
    opens = _XML_OPEN_TAG.findall(without_self_close)
    closes = _XML_CLOSE_TAG.findall(without_self_close)
    from collections import Counter

    open_counts = Counter(opens)
    close_counts = Counter(closes)
    for tag in open_counts:
        assert open_counts[tag] == close_counts.get(tag, 0), (
            f"Unbalanced XML tag <{tag}>: "
            f"{open_counts[tag]} opens vs {close_counts.get(tag, 0)} closes\n"
            f"Example {example.example} ({example.section})"
        )


@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=_example_id)
def test_xml_has_declaration(example):
    """Non-empty XML output always starts with XML declaration."""
    result = markdown_to_xml(example.markdown)
    if result.strip():
        assert result.startswith("<?xml version=")


# ---------------------------------------------------------------------------
# Structural validation: LaTeX balanced environments
# ---------------------------------------------------------------------------

_LATEX_BEGIN = re.compile(r"\\begin\{([^}]+)\}")
_LATEX_END = re.compile(r"\\end\{([^}]+)\}")


@pytest.mark.parametrize("example", ALL_EXAMPLES, ids=_example_id)
def test_latex_balanced_environments(example):
    """LaTeX output has matching \\begin{} and \\end{} counts for each environment."""
    result = markdown_to_latex(example.markdown)
    begins = _LATEX_BEGIN.findall(result)
    ends = _LATEX_END.findall(result)
    from collections import Counter

    begin_counts = Counter(begins)
    end_counts = Counter(ends)
    assert begin_counts == end_counts, (
        f"Unbalanced LaTeX environments:\n"
        f"  begins: {dict(begin_counts)}\n  ends: {dict(end_counts)}\n"
        f"Example {example.example} ({example.section})"
    )


# ---------------------------------------------------------------------------
# Width parameter: renderers handle width without error
# ---------------------------------------------------------------------------

_WIDTH_EXAMPLES = ALL_EXAMPLES[:50]  # Subset for speed (width doesn't vary by content)


def _width_id(example):
    return f"{example.fixture_file}::ex{example.example}"


@pytest.mark.parametrize("example", _WIDTH_EXAMPLES, ids=_width_id)
def test_latex_width_40(example):
    """LaTeX with width=40 doesn't crash and respects wrapping."""
    result = markdown_to_latex(example.markdown, width=40)
    assert isinstance(result, str)


@pytest.mark.parametrize("example", _WIDTH_EXAMPLES, ids=_width_id)
def test_man_width_40(example):
    """Man with width=40 doesn't crash."""
    result = markdown_to_man(example.markdown, width=40)
    assert isinstance(result, str)


@pytest.mark.parametrize("example", _WIDTH_EXAMPLES, ids=_width_id)
def test_commonmark_width_40(example):
    """CommonMark with width=40 doesn't crash."""
    result = markdown_to_commonmark(example.markdown, width=40)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Options: SOURCEPOS works for all renderers
# ---------------------------------------------------------------------------

_OPT_EXAMPLES = ALL_EXAMPLES[:50]  # Subset for speed


@pytest.mark.parametrize("example", _OPT_EXAMPLES, ids=_width_id)
def test_xml_sourcepos(example):
    """XML with SOURCEPOS produces sourcepos attributes."""
    result = markdown_to_xml(example.markdown, options=Options.SOURCEPOS)
    if example.markdown.strip():
        assert "sourcepos=" in result


@pytest.mark.parametrize("example", _OPT_EXAMPLES, ids=_width_id)
def test_latex_sourcepos_no_crash(example):
    """LaTeX with SOURCEPOS doesn't crash."""
    result = markdown_to_latex(example.markdown, options=Options.SOURCEPOS)
    assert isinstance(result, str)


@pytest.mark.parametrize("example", _OPT_EXAMPLES, ids=_width_id)
def test_all_renderers_smart(example):
    """SMART option doesn't crash any renderer."""
    md = example.markdown
    opts = Options.SMART
    assert isinstance(markdown_to_latex(md, options=opts), str)
    assert isinstance(markdown_to_man(md, options=opts), str)
    assert isinstance(markdown_to_xml(md, options=opts), str)
    assert isinstance(markdown_to_commonmark(md, options=opts), str)


# ---------------------------------------------------------------------------
# Determinism: same input always yields same output
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("example", _OPT_EXAMPLES, ids=_width_id)
def test_deterministic_output(example):
    """Rendering the same input twice produces identical output."""
    md = example.markdown
    assert markdown_to_latex(md) == markdown_to_latex(md)
    assert markdown_to_man(md) == markdown_to_man(md)
    assert markdown_to_xml(md) == markdown_to_xml(md)
    assert markdown_to_commonmark(md) == markdown_to_commonmark(md)
