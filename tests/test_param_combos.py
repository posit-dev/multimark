import itertools

import pytest

from multimark import (
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_commonmark,
    markdown_to_xml,
    Options,
)

# ---------------------------------------------------------------------------
# Test input that exercises many features at once
# ---------------------------------------------------------------------------

RICH_MARKDOWN = """\
# Heading

A paragraph with **bold**, *italic*, and `code`.

"Quotes" -- dashes --- and ellipsis...

Line one
Line two

- Item 1
- Item 2

```python
def hello():
    pass
```

Visit https://example.com for more.

<div>raw html</div>
"""


# ---------------------------------------------------------------------------
# Boolean flag cross-product (no-crash + output sanity)
# ---------------------------------------------------------------------------

BOOL_FLAGS = ["hardbreaks", "smart", "normalize", "unsafe", "footnotes"]

# Generate all 32 combinations of True/False for the 5 bool flags
BOOL_COMBOS = [
    dict(zip(BOOL_FLAGS, combo))
    for combo in itertools.product([False, True], repeat=len(BOOL_FLAGS))
]


def _combo_id(combo):
    active = [k for k, v in combo.items() if v]
    return "+".join(active) if active else "defaults"


@pytest.mark.parametrize("kwargs", BOOL_COMBOS, ids=_combo_id)
def test_html_bool_combos(kwargs):
    """HTML renderer handles all boolean flag combinations."""
    # sourcepos is also available for html/xml
    result = markdown_to_html(RICH_MARKDOWN, **kwargs)
    assert isinstance(result, str)
    assert len(result) > 0
    # Core content should always be present
    assert "Heading" in result


@pytest.mark.parametrize("kwargs", BOOL_COMBOS, ids=_combo_id)
def test_xml_bool_combos(kwargs):
    """XML renderer handles all boolean flag combinations."""
    result = markdown_to_xml(RICH_MARKDOWN, **kwargs)
    assert isinstance(result, str)
    assert "<?xml" in result


# For latex/man/commonmark, remove sourcepos (not accepted) — use subset
BOOL_FLAGS_NO_SOURCEPOS = ["hardbreaks", "smart", "normalize", "unsafe", "footnotes"]

BOOL_COMBOS_WIDTH = [
    dict(zip(BOOL_FLAGS_NO_SOURCEPOS, combo))
    for combo in itertools.product([False, True], repeat=len(BOOL_FLAGS_NO_SOURCEPOS))
]


@pytest.mark.parametrize("kwargs", BOOL_COMBOS_WIDTH, ids=_combo_id)
def test_latex_bool_combos(kwargs):
    """LaTeX renderer handles all boolean flag combinations."""
    result = markdown_to_latex(RICH_MARKDOWN, **kwargs)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.parametrize("kwargs", BOOL_COMBOS_WIDTH, ids=_combo_id)
def test_man_bool_combos(kwargs):
    """Man renderer handles all boolean flag combinations."""
    result = markdown_to_man(RICH_MARKDOWN, **kwargs)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.parametrize("kwargs", BOOL_COMBOS_WIDTH, ids=_combo_id)
def test_commonmark_bool_combos(kwargs):
    """CommonMark renderer handles all boolean flag combinations."""
    result = markdown_to_commonmark(RICH_MARKDOWN, **kwargs)
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Sourcepos interaction with other flags (html/xml only)
# ---------------------------------------------------------------------------

SOURCEPOS_COMBOS = [
    {"sourcepos": True},
    {"sourcepos": True, "smart": True},
    {"sourcepos": True, "hardbreaks": True},
    {"sourcepos": True, "unsafe": True},
    {"sourcepos": True, "smart": True, "hardbreaks": True, "unsafe": True},
]


@pytest.mark.parametrize("kwargs", SOURCEPOS_COMBOS)
def test_html_sourcepos_combos(kwargs):
    """Sourcepos combined with other flags produces valid output."""
    result = markdown_to_html(RICH_MARKDOWN, **kwargs)
    assert "data-sourcepos" in result


@pytest.mark.parametrize("kwargs", SOURCEPOS_COMBOS)
def test_xml_sourcepos_combos(kwargs):
    """Sourcepos with XML renderer."""
    result = markdown_to_xml(RICH_MARKDOWN, **kwargs)
    assert "sourcepos" in result


# ---------------------------------------------------------------------------
# Width parameter interactions (latex/man/commonmark)
# ---------------------------------------------------------------------------

WIDTH_VALUES = [0, 20, 40, 72, 80, 120]

WIDTH_RENDERERS = [
    ("latex", markdown_to_latex),
    ("man", markdown_to_man),
    ("commonmark", markdown_to_commonmark),
]


@pytest.mark.parametrize("width", WIDTH_VALUES)
@pytest.mark.parametrize("name,renderer", WIDTH_RENDERERS, ids=lambda x: x[0] if isinstance(x, tuple) else x)
def test_width_values(name, renderer, width):
    """Different width values produce valid output."""
    result = renderer(RICH_MARKDOWN, width=width)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.parametrize("width", WIDTH_VALUES)
def test_width_with_smart(width):
    """Width + smart flag interaction."""
    result = markdown_to_latex('"Hello" -- world\n', width=width, smart=True)
    assert isinstance(result, str)


@pytest.mark.parametrize("width", WIDTH_VALUES)
def test_width_with_hardbreaks(width):
    """Width + hardbreaks interaction."""
    result = markdown_to_commonmark("line1\nline2\n", width=width, hardbreaks=True)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Extensions combined with boolean flags
# ---------------------------------------------------------------------------

GFM_MARKDOWN = """\
| Feature | Status |
|---------|--------|
| Tables  | ~~old~~ new |
| Links   | https://example.com |

- [x] Done
- [ ] Todo

This is ~~deleted~~ text.
"""

EXTENSION_COMBOS = [
    ["table"],
    ["strikethrough"],
    ["autolink"],
    ["tagfilter"],
    ["tasklist"],
    ["table", "strikethrough"],
    ["table", "autolink", "tasklist"],
    ["table", "strikethrough", "autolink", "tagfilter", "tasklist"],
]

FLAG_COMBOS_FOR_EXT = [
    {},
    {"smart": True},
    {"unsafe": True},
    {"hardbreaks": True},
    {"smart": True, "unsafe": True},
    {"footnotes": True},
    {"smart": True, "unsafe": True, "hardbreaks": True, "footnotes": True},
]


@pytest.mark.parametrize("flags", FLAG_COMBOS_FOR_EXT)
@pytest.mark.parametrize("exts", EXTENSION_COMBOS, ids=lambda e: "+".join(e))
def test_html_extensions_with_flags(exts, flags):
    """Extensions combined with various flag combos produce valid HTML."""
    result = markdown_to_html(GFM_MARKDOWN, extensions=exts, **flags)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.parametrize("flags", FLAG_COMBOS_FOR_EXT)
@pytest.mark.parametrize("exts", EXTENSION_COMBOS, ids=lambda e: "+".join(e))
def test_latex_extensions_with_flags(exts, flags):
    """Extensions combined with flags produce valid LaTeX."""
    result = markdown_to_latex(GFM_MARKDOWN, extensions=exts, **flags)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.parametrize("exts", EXTENSION_COMBOS, ids=lambda e: "+".join(e))
def test_xml_extensions(exts):
    """Extensions produce valid XML output."""
    result = markdown_to_xml(GFM_MARKDOWN, extensions=exts)
    assert isinstance(result, str)
    assert "<?xml" in result


# ---------------------------------------------------------------------------
# Options bitmask combined with named flags
# ---------------------------------------------------------------------------

BITMASK_COMBOS = [
    (Options.SMART, {"hardbreaks": True}),
    (Options.HARDBREAKS, {"smart": True}),
    (Options.UNSAFE, {"smart": True, "hardbreaks": True}),
    (Options.SOURCEPOS, {"smart": True}),
    (Options.SMART | Options.UNSAFE, {"hardbreaks": True}),
    (Options.VALIDATE_UTF8, {"smart": True, "unsafe": True}),
    (Options.FOOTNOTES, {"smart": True}),
]


@pytest.mark.parametrize("opts,kwargs", BITMASK_COMBOS)
def test_bitmask_combined_with_named_flags(opts, kwargs):
    """Raw options bitmask OR'd with named boolean flags."""
    result = markdown_to_html(RICH_MARKDOWN, options=opts, **kwargs)
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Verify flag semantics (output correctness, not just no-crash)
# ---------------------------------------------------------------------------


class TestFlagSemantics:
    """Verify that flags actually change the output as expected."""

    def test_smart_produces_curly_quotes_html(self):
        result = markdown_to_html('"Hello"\n', smart=True)
        assert "\u201c" in result  # left double quote
        assert "\u201d" in result  # right double quote

    def test_smart_off_keeps_straight_quotes_html(self):
        result = markdown_to_html('"Hello"\n', smart=False)
        assert "&quot;" in result or '"' in result

    def test_hardbreaks_produces_br(self):
        result = markdown_to_html("line1\nline2\n", hardbreaks=True)
        assert "<br" in result

    def test_no_hardbreaks_no_br(self):
        result = markdown_to_html("line1\nline2\n", hardbreaks=False)
        assert "<br" not in result

    def test_unsafe_passes_raw_html(self):
        result = markdown_to_html("<div>raw</div>\n", unsafe=True)
        assert "<div>raw</div>" in result

    def test_safe_strips_raw_html(self):
        result = markdown_to_html("<div>raw</div>\n", unsafe=False)
        assert "<div>" not in result

    def test_sourcepos_adds_attributes(self):
        result = markdown_to_html("Hello\n", sourcepos=True)
        assert "data-sourcepos" in result

    def test_no_sourcepos_no_attributes(self):
        result = markdown_to_html("Hello\n", sourcepos=False)
        assert "data-sourcepos" not in result

    def test_smart_em_dash(self):
        result = markdown_to_html("a---b\n", smart=True)
        assert "\u2014" in result  # em dash

    def test_smart_en_dash(self):
        result = markdown_to_html("a--b\n", smart=True)
        assert "\u2013" in result  # en dash

    def test_smart_ellipsis(self):
        result = markdown_to_html("a...\n", smart=True)
        assert "\u2026" in result  # ellipsis

    def test_footnotes_flag_enables_footnotes(self):
        md = "Text[^1]\n\n[^1]: Footnote content\n"
        result = markdown_to_html(md, footnotes=True)
        assert "footnote" in result.lower() or "fn" in result.lower()

    def test_footnotes_off_no_footnote_markup(self):
        md = "Text[^1]\n\n[^1]: Footnote content\n"
        result = markdown_to_html(md, footnotes=False)
        # Without footnotes, no <sup>/<section class="footnotes"> markup
        assert "<section" not in result
        assert "<sup>" not in result

    def test_width_wraps_latex(self):
        long_line = "word " * 50 + "\n"
        narrow = markdown_to_latex(long_line, width=40)
        wide = markdown_to_latex(long_line, width=0)
        # Narrow should have more newlines due to wrapping
        assert narrow.count("\n") >= wide.count("\n")

    def test_width_wraps_commonmark(self):
        long_line = "word " * 50 + "\n"
        narrow = markdown_to_commonmark(long_line, width=40)
        wide = markdown_to_commonmark(long_line, width=0)
        assert narrow.count("\n") >= wide.count("\n")


# ---------------------------------------------------------------------------
# Extension semantics verification
# ---------------------------------------------------------------------------


class TestExtensionSemantics:
    """Verify extensions produce expected structural output."""

    def test_table_creates_table_element(self):
        md = "| a |\n|---|\n| b |\n"
        with_ext = markdown_to_html(md, extensions=["table"])
        without_ext = markdown_to_html(md)
        assert "<table>" in with_ext
        assert "<table>" not in without_ext

    def test_strikethrough_creates_del(self):
        md = "~~deleted~~\n"
        with_ext = markdown_to_html(md, extensions=["strikethrough"])
        without_ext = markdown_to_html(md)
        assert "<del>" in with_ext
        assert "<del>" not in without_ext

    def test_autolink_creates_link(self):
        md = "See https://example.com here.\n"
        with_ext = markdown_to_html(md, extensions=["autolink"])
        without_ext = markdown_to_html(md)
        assert '<a href="https://example.com">' in with_ext
        assert "<a " not in without_ext

    def test_tasklist_creates_checkbox(self):
        md = "- [x] Done\n- [ ] Todo\n"
        with_ext = markdown_to_html(md, extensions=["tasklist"])
        without_ext = markdown_to_html(md)
        assert '<input type="checkbox"' in with_ext
        assert '<input type="checkbox"' not in without_ext

    def test_tagfilter_blocks_dangerous_tags(self):
        md = "<textarea>evil</textarea>\n"
        with_ext = markdown_to_html(md, extensions=["tagfilter"], unsafe=True)
        without_ext = markdown_to_html(md, unsafe=True)
        assert "&lt;textarea>" in with_ext
        assert "<textarea>" in without_ext

    def test_extensions_do_not_affect_non_gfm_content(self):
        """Regular markdown is identical with or without extensions."""
        md = "**bold** and *italic*\n"
        with_ext = markdown_to_html(md, extensions=["table", "strikethrough"])
        without_ext = markdown_to_html(md)
        assert with_ext == without_ext
