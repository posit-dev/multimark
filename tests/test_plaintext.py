"""Smoke tests for plaintext rendering, options, and line wrapping."""
from multimark import Options, markdown_to_plaintext

# --- Rendering ---


def test_removes_markdown_formatting():
    md = "# Title\n\n**bold** and *italic* with `code` and [link](https://example.com).\n"
    assert markdown_to_plaintext(md) == "Title\n\nbold and italic with code and link.\n"


def test_extensions():
    result = markdown_to_plaintext("~~deleted~~\n", extensions=["strikethrough"])
    assert result == "~deleted~\n"


def test_raw_html_omitted():
    md = "Hello <b>world</b>!\n\n<div>hidden</div>\n"
    assert markdown_to_plaintext(md, unsafe=True) == "Hello world!\n"


# --- Width parameter ---


def test_width_wraps_output():
    result = markdown_to_plaintext("word " * 100, width=40)
    lines = result.splitlines()
    assert len(lines) > 1
    assert all(len(line) <= 40 for line in lines)


def test_width_zero_does_not_wrap():
    assert markdown_to_plaintext("word " * 100).count("\n") == 1


def test_hardbreaks_disables_width_wrapping():
    md = "word " * 20 + "\nnext\n"
    result = markdown_to_plaintext(md, width=10, hardbreaks=True)
    assert result == markdown_to_plaintext(md)


# --- Edge cases and options ---


def test_empty_input():
    assert markdown_to_plaintext("") == "\n"


def test_unicode_preserved():
    assert "你好世界" in markdown_to_plaintext("你好世界\n")


def test_smart_option():
    result = markdown_to_plaintext('"Hello"\n', options=Options.SMART)
    assert "\u201c" in result
