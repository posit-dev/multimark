import pytest

from multimark import (
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_commonmark,
    markdown_to_xml,
)

ALL_RENDERERS = [
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_commonmark,
    markdown_to_xml,
]


def _ids(fn):
    return fn.__name__


# ---------------------------------------------------------------------------
# Deeply nested structures (cmark limits nesting to prevent stack overflow)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_deeply_nested_blockquotes(renderer):
    """Deeply nested blockquotes don't crash (cmark limits depth)."""
    md = ">" * 10000 + " deep\n"
    result = renderer(md)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_deeply_nested_lists(renderer):
    """Deeply nested lists don't crash."""
    md = ""
    for i in range(500):
        md += " " * (i * 2) + "- item\n"
    result = renderer(md)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_deeply_nested_emphasis(renderer):
    """Many nested emphasis markers don't cause exponential blowup."""
    md = "*" * 5000 + "a" + "*" * 5000 + "\n"
    result = renderer(md)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_deeply_nested_links(renderer):
    """Many nested link openers don't cause exponential blowup."""
    md = "[" * 5000 + "a" + "]" * 5000 + "\n"
    result = renderer(md)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_many_link_closers(renderer):
    """Pattern that could cause backtracking in naive parsers."""
    md = "[a](" + ")" * 5000 + "\n"
    result = renderer(md)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_many_backticks(renderer):
    """Long runs of backticks don't cause quadratic scanning."""
    md = "`" * 10000 + "a" + "`" * 10000 + "\n"
    result = renderer(md)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Adversarial / fuzz-like inputs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_null_bytes(renderer):
    """Embedded null bytes are handled (replaced with U+FFFD)."""
    md = "hello\x00world\x00end\n"
    result = renderer(md)
    assert isinstance(result, str)
    assert "\x00" not in result


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_all_control_characters(renderer):
    """Control characters don't crash the renderer."""
    md = "".join(chr(i) for i in range(32)) + "\n"
    result = renderer(md)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_only_newlines(renderer):
    """Document of only newlines doesn't crash."""
    md = "\n" * 10000
    result = renderer(md)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_very_long_line(renderer):
    """A single extremely long line doesn't crash."""
    md = "a" * 100000 + "\n"
    result = renderer(md)
    assert isinstance(result, str)
    assert "a" in result


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_many_headings(renderer):
    """Thousands of headings don't crash."""
    md = "".join(f"# Heading {i}\n\n" for i in range(1000))
    result = renderer(md)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_alternating_code_blocks(renderer):
    """Many alternating fenced code blocks."""
    md = "".join("```\ncode\n```\n\n" for _ in range(500))
    result = renderer(md)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_unicode_boundaries(renderer):
    """Surrogate-adjacent Unicode codepoints."""
    # U+FFFF (last BMP), U+10000 (first supplementary)
    md = "\uffff \U00010000 \U0010ffff\n"
    result = renderer(md)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_mixed_line_endings(renderer):
    """Mix of \\n, \\r\\n, and bare \\r."""
    md = "line1\r\nline2\rline3\nline4\n"
    result = renderer(md)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Repeated processing (exercise memory management)
# ---------------------------------------------------------------------------


def test_repeated_rendering_no_crash():
    """Render the same document many times to exercise alloc/free cycles."""
    md = "# Hello\n\nThis is **bold** and *italic* with [link](http://x.com)\n"
    for _ in range(10000):
        result = markdown_to_html(md)
    assert "<h1>" in result


def test_many_different_documents():
    """Process many unique documents to stress memory management."""
    for i in range(5000):
        md = f"# Doc {i}\n\nParagraph {i} with **bold {i}**.\n"
        result = markdown_to_html(md)
        assert f"Doc {i}" in result
