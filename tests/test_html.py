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

