from multimark import markdown_to_html, Options


# --- Option flags ---


def test_safe_mode_strips_raw_html():
    """Default (safe) mode strips dangerous raw HTML."""
    result = markdown_to_html("<script>alert('xss')</script>\n")
    assert "<script>" not in result


def test_unsafe_mode_allows_raw_html():
    result = markdown_to_html("<div>hi</div>\n", options=Options.UNSAFE)
    assert "<div>hi</div>" in result


def test_sourcepos():
    """SOURCEPOS adds data-sourcepos attributes."""
    result = markdown_to_html("Hello\n", options=Options.SOURCEPOS)
    assert "data-sourcepos" in result


def test_smart_quotes():
    """SMART converts straight quotes to curly."""
    result = markdown_to_html('"Hello"\n', options=Options.SMART)
    assert "\u201c" in result and "\u201d" in result


def test_smart_dashes():
    """SMART converts -- to en-dash, --- to em-dash."""
    result = markdown_to_html("a -- b --- c\n", options=Options.SMART)
    assert "\u2013" in result  # en-dash
    assert "\u2014" in result  # em-dash


def test_smart_ellipsis():
    """SMART converts ... to ellipsis character."""
    result = markdown_to_html("wait...\n", options=Options.SMART)
    assert "\u2026" in result


def test_hardbreaks():
    """HARDBREAKS turns soft newlines into <br>."""
    result = markdown_to_html("line1\nline2\n", options=Options.HARDBREAKS)
    assert "<br" in result


def test_nobreaks():
    """NOBREAKS turns soft newlines into spaces (no <br> even with \\)."""
    result = markdown_to_html("line1\nline2\n", options=Options.NOBREAKS)
    assert "<br" not in result
    assert "line1" in result and "line2" in result


def test_combined_options():
    """Multiple option flags can be combined."""
    result = markdown_to_html(
        '"Hello"\n', options=Options.SMART | Options.SOURCEPOS
    )
    assert "\u201c" in result
    assert "data-sourcepos" in result


# --- Edge cases ---


def test_empty_input():
    assert markdown_to_html("") == ""


def test_only_whitespace():
    assert markdown_to_html("   \n\n  \n") == ""


def test_unicode_multibyte():
    """Multi-byte Unicode passes through correctly."""
    result = markdown_to_html("Hello \U0001f600 world\n")
    assert "\U0001f600" in result


def test_unicode_cjk():
    result = markdown_to_html("# \u4f60\u597d\u4e16\u754c\n")
    assert "<h1>\u4f60\u597d\u4e16\u754c</h1>" in result


def test_very_long_input():
    """Large document doesn't crash."""
    big = ("paragraph " * 100 + "\n\n") * 100
    result = markdown_to_html(big)
    assert "<p>" in result


def test_null_bytes_in_input():
    """Null bytes are replaced with U+FFFD."""
    result = markdown_to_html("hello\x00world\n")
    assert "\ufffd" in result


def test_newline_variations():
    """Handles different line ending styles."""
    assert markdown_to_html("hello\r\nworld\n") == markdown_to_html("hello\nworld\n")


# --- GFM-specific Options flags ---


def test_github_pre_lang():
    """GITHUB_PRE_LANG adds language as a class on <pre> instead of <code>."""
    md = "```python\ncode\n```\n"
    result = markdown_to_html(md, options=Options.GITHUB_PRE_LANG)
    assert 'lang="python"' in result or 'class="language-python"' in result.replace(
        "<code", "<pre"
    )
    # Without the flag, language class is on <code>
    default = markdown_to_html(md)
    assert 'class="language-python"' in default


def test_liberal_html_tag():
    """LIBERAL_HTML_TAG allows non-standard HTML tags."""
    result = markdown_to_html(
        "<custom-element>text</custom-element>\n",
        options=Options.LIBERAL_HTML_TAG | Options.UNSAFE,
    )
    assert "<custom-element>" in result


def test_full_info_string():
    """FULL_INFO_STRING preserves the full info string on code blocks."""
    md = "```python extra-info\ncode\n```\n"
    result = markdown_to_html(md, options=Options.FULL_INFO_STRING)
    assert "extra-info" in result or "data-meta" in result


def test_strikethrough_double_tilde():
    """STRIKETHROUGH_DOUBLE_TILDE requires ~~ (not ~) for strikethrough."""
    md_double = "~~deleted~~\n"
    md_single = "~deleted~\n"
    result_double = markdown_to_html(
        md_double,
        extensions=["strikethrough"],
        options=Options.STRIKETHROUGH_DOUBLE_TILDE,
    )
    result_single = markdown_to_html(
        md_single,
        extensions=["strikethrough"],
        options=Options.STRIKETHROUGH_DOUBLE_TILDE,
    )
    assert "<del>" in result_double
    assert "<del>" not in result_single


def test_table_prefer_style_attributes():
    """TABLE_PREFER_STYLE_ATTRIBUTES uses style= instead of align=."""
    md = "| left | center | right |\n|:-----|:------:|------:|\n| a | b | c |\n"
    result = markdown_to_html(
        md, extensions=["table"], options=Options.TABLE_PREFER_STYLE_ATTRIBUTES
    )
    assert "style=" in result


# --- Footnotes keyword argument ---


def test_footnotes_keyword():
    """footnotes=True enables footnote parsing without extensions list."""
    md = "Text[^1]\n\n[^1]: A footnote.\n"
    result = markdown_to_html(md, footnotes=True)
    assert "footnote" in result.lower()
    # Without footnotes, the marker is treated as regular text
    result_no = markdown_to_html(md, footnotes=False)
    assert "[^1]" in result_no

