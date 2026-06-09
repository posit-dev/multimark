from multimark import markdown_to_man, Options


# --- Width parameter ---


def test_width_wraps_output():
    """Non-zero width wraps long lines."""
    long_text = "word " * 100 + "\n"
    result = markdown_to_man(long_text, width=60)
    content_lines = [l for l in result.split("\n") if "word" in l]
    assert all(len(l) <= 60 for l in content_lines)


def test_width_zero_no_wrapping():
    long_text = "word " * 100 + "\n"
    result = markdown_to_man(long_text, width=0)
    content_lines = [l for l in result.split("\n") if "word" in l]
    assert any(len(l) > 60 for l in content_lines)


# --- Man format-specific ---


def test_heading_levels():
    """H1 uses .SH, H2 uses .SS."""
    assert ".SH" in markdown_to_man("# Top\n")
    assert ".SS" in markdown_to_man("## Sub\n")


def test_bold_formatting():
    assert "\\f[B]" in markdown_to_man("**bold**\n")


def test_italic_formatting():
    assert "\\f[I]" in markdown_to_man("*italic*\n")


def test_paragraph_macro():
    result = markdown_to_man("First para\n\nSecond para\n")
    assert ".PP" in result


def test_empty_input():
    assert markdown_to_man("") == "\n"


def test_unicode_passthrough():
    result = markdown_to_man("éàü\n")
    assert "é" in result


def test_smart_option():
    """SMART option produces typographic groff escapes."""
    result = markdown_to_man('"Hello"\n', options=Options.SMART)
    # Man uses \[lq] and \[rq] for curly quotes
    assert "\\[lq]" in result or "\u201c" in result

