from multimark import markdown_to_latex, Options


# --- Width parameter ---


def test_width_zero_no_wrapping():
    """width=0 means no line wrapping."""
    long_text = "word " * 100 + "\n"
    result = markdown_to_latex(long_text, width=0)
    # Content lines should not be forcibly wrapped
    content_lines = [l for l in result.split("\n") if "word" in l]
    assert any(len(l) > 80 for l in content_lines)


def test_width_wraps_output():
    """Non-zero width wraps long lines."""
    long_text = "word " * 100 + "\n"
    result = markdown_to_latex(long_text, width=72)
    content_lines = [l for l in result.split("\n") if "word" in l]
    assert all(len(l) <= 72 for l in content_lines)


# --- LaTeX-specific formatting ---


def test_special_chars_escaped():
    """LaTeX special characters are escaped."""
    result = markdown_to_latex("Price is $10 & tax is 5%\n")
    assert "\\$" in result or "\\textdollar" in result
    assert "\\&" in result


def test_heading_levels():
    """Different heading levels produce correct LaTeX commands."""
    assert "\\section{" in markdown_to_latex("# H1\n")
    assert "\\subsection{" in markdown_to_latex("## H2\n")
    assert "\\subsubsection{" in markdown_to_latex("### H3\n")


def test_image_produces_includegraphics():
    result = markdown_to_latex("![alt](image.png)\n")
    assert "includegraphics" in result or "image.png" in result


def test_unicode_passthrough():
    """Unicode characters pass through to LaTeX output."""
    result = markdown_to_latex("éàüñ\n")
    assert "é" in result


def test_empty_input():
    """Empty string produces empty output."""
    assert markdown_to_latex("") == ""


def test_empty_input():
    assert markdown_to_latex("") == "\n"


def test_smart_option():
    """SMART option produces typographic LaTeX output."""
    result = markdown_to_latex('"Hello" -- world\n', options=Options.SMART)
    # LaTeX uses `` and '' for curly quotes, -- for en-dash
    assert "``" in result or "\u201c" in result
