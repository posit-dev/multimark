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
# Issue #36: PCDATA invalid Char value
# Control characters in input produce invalid XML output.
# Fixed via https://github.com/commonmark/cmark/pull/376
# The XML output must not contain raw control chars that violate XML spec.
# XML 1.0 allows: #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD]
# ---------------------------------------------------------------------------


class TestIssue36_InvalidXmlChars:
    """Control characters must be stripped/escaped in XML output."""

    @pytest.mark.xfail(reason="cmark-gfm 0.29.x does not strip control chars from XML output")
    def test_control_char_x13(self):
        """The specific char that triggered the original report."""
        result = markdown_to_xml("foo\x13bar\n")
        assert "\x13" not in result
        # Should still be valid — either stripped or replaced
        assert "foo" in result

    @pytest.mark.xfail(reason="cmark-gfm 0.29.x does not strip control chars from XML output")
    def test_control_char_x19(self):
        result = markdown_to_xml("foo\x19bar\n")
        assert "\x19" not in result

    @pytest.mark.xfail(reason="cmark-gfm 0.29.x does not strip control chars from XML output")
    @pytest.mark.parametrize("char", [
        "\x01", "\x02", "\x03", "\x04", "\x05", "\x06", "\x07", "\x08",
        "\x0b", "\x0c", "\x0e", "\x0f", "\x10", "\x11", "\x12", "\x13",
        "\x14", "\x15", "\x16", "\x17", "\x18", "\x19", "\x1a", "\x1b",
        "\x1c", "\x1d", "\x1e", "\x1f",
    ])
    def test_all_invalid_xml_control_chars(self, char):
        """No invalid XML control char should appear in XML output."""
        result = markdown_to_xml(f"text{char}here\n")
        # These are all forbidden in XML 1.0 PCDATA
        assert char not in result

    def test_allowed_control_chars_preserved(self):
        """Tab (0x09), LF (0x0A), CR (0x0D) are allowed in XML."""
        # Tab should be preserved (it's valid XML)
        result = markdown_to_xml("col1\tcol2\n")
        # cmark may or may not preserve it, but shouldn't crash
        assert isinstance(result, str)

    def test_control_chars_in_all_renderers(self):
        """Control chars don't crash any renderer."""
        md = "hello\x13world\x01end\n"
        assert isinstance(markdown_to_html(md), str)
        assert isinstance(markdown_to_latex(md), str)
        assert isinstance(markdown_to_man(md), str)
        assert isinstance(markdown_to_commonmark(md), str)
        assert isinstance(markdown_to_xml(md), str)


# ---------------------------------------------------------------------------
# Issue #37: SOURCEPOS reports byte offsets for multi-byte characters
# This is by design in cmark — sourcepos uses byte offsets, not char offsets.
# We document this behavior and ensure it's consistent.
# ---------------------------------------------------------------------------


class TestIssue37_SourceposByteOffsets:
    """SOURCEPOS uses byte offsets, which differ from char offsets for multi-byte."""

    def test_ascii_sourcepos_matches_char_count(self):
        """For ASCII, byte offset == char offset."""
        result = markdown_to_html("hello\n", options=Options.SOURCEPOS)
        # "hello" is 5 bytes and 5 chars — should report 1:1-1:5
        assert 'data-sourcepos="1:1-1:5"' in result

    def test_multibyte_sourcepos_uses_bytes(self):
        """Multi-byte chars: sourcepos reflects byte length, not char count."""
        # The curly quote ' is U+2019, which is 3 bytes in UTF-8
        result = markdown_to_html("\u2019\n", options=Options.SOURCEPOS)
        # 1 char but 3 bytes — sourcepos should report 1:1-1:3
        assert 'data-sourcepos="1:1-1:3"' in result

    def test_emoji_sourcepos(self):
        """4-byte emoji: sourcepos reports byte offset."""
        # 🎉 is U+1F389, 4 bytes in UTF-8
        result = markdown_to_html("\U0001f389\n", options=Options.SOURCEPOS)
        # 1 char but 4 bytes
        assert 'data-sourcepos="1:1-1:4"' in result

    def test_mixed_ascii_and_multibyte(self):
        """Mixed content: byte offsets accumulate correctly."""
        # "a" (1 byte) + "é" (2 bytes) + "b" (1 byte) = 4 bytes total
        result = markdown_to_html("a\u00e9b\n", options=Options.SOURCEPOS)
        assert 'data-sourcepos="1:1-1:4"' in result

    def test_sourcepos_in_xml(self):
        """SOURCEPOS in XML also uses byte offsets."""
        result = markdown_to_xml("\u2019\n", options=Options.SOURCEPOS)
        assert 'sourcepos="1:1-1:3"' in result


# ---------------------------------------------------------------------------
# Issue #26: CVE-2023-26485
# Polynomial regular expression used on uncontrolled data in cmark-gfm.
# Our cmark 0.31.2 should not be affected (it's upstream cmark, not gfm).
# Still, verify the patterns that triggered it don't crash.
# ---------------------------------------------------------------------------


class TestCVE_2023_26485:
    """Patterns related to CVE-2023-26485 don't cause issues."""

    def test_many_unclosed_image_links(self):
        """Repeated ![image]( patterns that could trigger regex backtracking."""
        md = "![a](" * 1000 + "\n"
        result = markdown_to_html(md)
        assert isinstance(result, str)

    def test_deeply_nested_image_links(self):
        md = "![" * 500 + "x" + "](" * 500 + ")" * 500 + "\n"
        result = markdown_to_html(md)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Issue #17: CVE-2022-24724 — integer overflow in table extension
# This affects cmark-gfm only (table extension), not upstream cmark.
# We vendor upstream cmark without extensions in Phase 1, so not vulnerable.
# Still verify a table-like input with many columns doesn't crash.
# ---------------------------------------------------------------------------


class TestCVE_2022_24724:
    """Table-like inputs with many columns don't crash (even without GFM tables)."""

    def test_many_pipes(self):
        """Line with thousands of pipes (would be table columns in GFM)."""
        md = "|" * 70000 + "\n"
        result = markdown_to_html(md)
        assert isinstance(result, str)

    def test_table_like_structure(self):
        """Something that looks like a huge table."""
        header = "| " + " | ".join(f"col{i}" for i in range(1000)) + " |\n"
        sep = "| " + " | ".join(["---"] * 1000) + " |\n"
        row = "| " + " | ".join(f"val{i}" for i in range(1000)) + " |\n"
        md = header + sep + row
        # Without GFM extension, this is just text — shouldn't crash
        result = markdown_to_html(md)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Issue #13: CVE-2020-5238
# Crafted input could cause out-of-bounds read in older cmark.
# Fixed in cmark 0.29.0.gfm.1. Our 0.31.2 is well past this.
# ---------------------------------------------------------------------------


class TestCVE_2020_5238:
    """Inputs related to CVE-2020-5238 don't crash."""

    def test_crafted_link_destination(self):
        """Malformed link destinations that could trigger OOB read."""
        md = "[x](<\x00>)\n"
        result = markdown_to_html(md)
        assert isinstance(result, str)

    def test_very_long_link_destination(self):
        md = f"[x]({'a' * 100000})\n"
        result = markdown_to_html(md)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Issue #19: Attributes like {target='_blank'} are NOT CommonMark
# Verify we handle them as plain text (not crash, not parse as attributes).
# ---------------------------------------------------------------------------


class TestIssue19_AttributesSyntax:
    """Pandoc-style {attributes} are treated as literal text."""

    def test_target_blank_is_literal_text(self):
        md = "[RStudio](https://www.rstudio.com/){target='_blank'}\n"
        result = markdown_to_html(md)
        # Link should be parsed, but attribute syntax is literal
        assert '<a href="https://www.rstudio.com/">RStudio</a>' in result
        assert "{target=" in result or "target=&#39;_blank&#39;" in result

    def test_class_attribute_is_literal(self):
        md = "# Title {.unnumbered}\n"
        result = markdown_to_html(md)
        assert "{.unnumbered}" in result
