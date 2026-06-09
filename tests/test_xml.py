from multimark import markdown_to_xml, Options


# --- XML structure ---


def test_xml_declaration():
    """Output starts with XML declaration."""
    result = markdown_to_xml("Hello\n")
    assert result.startswith("<?xml version=\"1.0\"")


def test_doctype():
    result = markdown_to_xml("Hello\n")
    assert "<!DOCTYPE document SYSTEM \"CommonMark.dtd\">" in result


def test_document_root():
    result = markdown_to_xml("Hello\n")
    assert "<document" in result
    assert "xmlns=\"http://commonmark.org/xml/1.0\"" in result


def test_well_formed_tags():
    """All opened tags are closed."""
    result = markdown_to_xml("**bold** and *italic*\n")
    assert result.count("<paragraph") == result.count("</paragraph>")
    assert result.count("<strong") == result.count("</strong>")
    assert result.count("<emph") == result.count("</emph>")


# --- Options ---


def test_sourcepos():
    """SOURCEPOS adds sourcepos attributes."""
    result = markdown_to_xml("Hello\n", options=Options.SOURCEPOS)
    assert "sourcepos=\"" in result


# --- Edge cases ---


def test_empty_input():
    result = markdown_to_xml("")
    assert "<?xml" in result
    assert "<document" in result


def test_unicode_in_xml():
    result = markdown_to_xml("你好\n")
    assert "你好" in result


def test_special_xml_chars_escaped():
    """Characters like & and < in text are escaped in XML output."""
    result = markdown_to_xml("a & b < c\n")
    assert "&amp;" in result
    assert "&lt;" in result
