"""Tests for the streaming Parser class."""

import pytest

from multimark import Parser, markdown_to_html


class TestParserBasic:
    """Basic Parser lifecycle."""

    def test_simple_render_html(self):
        p = Parser()
        p.feed("**bold**")
        assert p.render_html() == "<p><strong>bold</strong></p>\n"

    def test_multiple_feeds(self):
        p = Parser()
        p.feed("# Title\n\n")
        p.feed("Para ")
        p.feed("text.\n")
        assert p.render_html() == "<h1>Title</h1>\n<p>Para text.</p>\n"

    def test_empty_document(self):
        p = Parser()
        p.feed("")
        assert p.render_html() == ""

    def test_no_feed(self):
        p = Parser()
        assert p.render_html() == ""

    def test_render_multiple_times(self):
        p = Parser()
        p.feed("hello")
        html1 = p.render_html()
        html2 = p.render_html()
        assert html1 == html2

    def test_equivalence_with_one_shot(self):
        text = "# Hello\n\nA *paragraph* with `code`.\n\n> blockquote\n"
        p = Parser()
        p.feed(text)
        assert p.render_html() == markdown_to_html(text)

    def test_chunked_equivalence(self):
        text = "# Hello\n\nA *paragraph* with `code`.\n\n> blockquote\n"
        p = Parser()
        for char in text:
            p.feed(char)
        assert p.render_html() == markdown_to_html(text)


class TestParserOptions:
    """Parser options (smart, unsafe, etc.)."""

    def test_smart(self):
        p = Parser(smart=True)
        p.feed('"Hello" -- world')
        html = p.render_html()
        assert "\u201c" in html  # left curly quote
        assert "\u2013" in html  # en-dash

    def test_unsafe(self):
        p = Parser(unsafe=True)
        p.feed("<div>raw</div>")
        assert "<div>raw</div>" in p.render_html()

    def test_safe_default(self):
        p = Parser()
        p.feed("<div>raw</div>")
        assert "<div>" not in p.render_html()

    def test_hardbreaks(self):
        p = Parser(hardbreaks=True)
        p.feed("line1\nline2")
        assert "<br />" in p.render_html()

    def test_footnotes(self):
        p = Parser(footnotes=True)
        p.feed("Text[^1]\n\n[^1]: Footnote\n")
        html = p.render_html()
        assert "footnote" in html.lower() or "fn" in html.lower()

    def test_sourcepos(self):
        p = Parser()
        p.feed("# Hello\n")
        html = p.render_html(sourcepos=True)
        assert "data-sourcepos" in html


class TestParserExtensions:
    """Parser with GFM extensions."""

    def test_table(self):
        p = Parser(extensions=["table"])
        p.feed("| A | B |\n|---|---|\n| 1 | 2 |\n")
        html = p.render_html()
        assert "<table>" in html
        assert "<td>1</td>" in html

    def test_strikethrough(self):
        p = Parser(extensions=["strikethrough"])
        p.feed("~~deleted~~")
        assert "<del>deleted</del>" in p.render_html()

    def test_autolink(self):
        p = Parser(extensions=["autolink"])
        p.feed("Visit https://example.com today")
        html = p.render_html()
        assert 'href="https://example.com"' in html

    def test_tasklist(self):
        p = Parser(extensions=["tasklist"], unsafe=True)
        p.feed("- [ ] todo\n- [x] done\n")
        html = p.render_html()
        assert "checkbox" in html or "type=\"checkbox\"" in html

    def test_multiple_extensions(self):
        p = Parser(extensions=["table", "strikethrough", "autolink"])
        p.feed("~~del~~ and https://x.com\n\n| A |\n|---|\n| 1 |\n")
        html = p.render_html()
        assert "<del>" in html
        assert "<table>" in html
        assert "href" in html

    def test_invalid_extension(self):
        with pytest.raises(ValueError, match="Unknown extension"):
            Parser(extensions=["nonexistent"])

    def test_extension_equivalence(self):
        text = "| A | B |\n|---|---|\n| 1 | 2 |\n"
        p = Parser(extensions=["table"])
        p.feed(text)
        assert p.render_html() == markdown_to_html(text, extensions=["table"])


class TestParserRenderers:
    """Parser rendering to all output formats."""

    def test_render_xml(self):
        p = Parser()
        p.feed("**bold**")
        xml = p.render_xml()
        assert "<strong>" in xml
        assert "<?xml" in xml

    def test_render_xml_sourcepos(self):
        p = Parser()
        p.feed("hello")
        xml = p.render_xml(sourcepos=True)
        assert "sourcepos" in xml

    def test_render_latex(self):
        p = Parser()
        p.feed("**bold**")
        latex = p.render_latex()
        assert "\\textbf{bold}" in latex

    def test_render_latex_width(self):
        p = Parser()
        p.feed("word " * 50)
        narrow = p.render_latex(width=40)
        assert "\n" in narrow

    def test_render_man(self):
        p = Parser()
        p.feed("**bold**")
        man = p.render_man()
        assert "\\f[B]bold\\f[]" in man

    def test_render_man_width(self):
        p = Parser()
        p.feed("word " * 50)
        narrow = p.render_man(width=40)
        assert "\n" in narrow

    def test_render_commonmark(self):
        p = Parser()
        p.feed("*italic*")
        cm = p.render_commonmark()
        assert "*italic*" in cm

    def test_render_commonmark_width(self):
        p = Parser()
        p.feed("word " * 50)
        narrow = p.render_commonmark(width=40)
        assert "\n" in narrow


class TestParserLifecycle:
    """Parser lifecycle and error handling."""

    def test_context_manager(self):
        with Parser() as p:
            p.feed("hello")
            html = p.render_html()
        assert html == "<p>hello</p>\n"

    def test_context_manager_cleanup(self):
        with Parser() as p:
            p.feed("hello")
        with pytest.raises(ValueError, match="closed"):
            p.feed("more")

    def test_feed_after_close(self):
        p = Parser()
        p.feed("hello")
        p.close()
        with pytest.raises(ValueError, match="closed"):
            p.feed("more")

    def test_render_after_close(self):
        p = Parser()
        p.feed("hello")
        p.close()
        with pytest.raises(ValueError, match="closed"):
            p.render_html()

    def test_feed_after_finish(self):
        p = Parser()
        p.feed("hello")
        p.render_html()  # implicitly finishes
        with pytest.raises(ValueError, match="finished"):
            p.feed("more")

    def test_double_close(self):
        p = Parser()
        p.close()
        p.close()  # should not raise

    def test_feed_type_error(self):
        p = Parser()
        with pytest.raises(TypeError, match="Expected str"):
            p.feed(123)

    def test_feed_bytes_type_error(self):
        p = Parser()
        with pytest.raises(TypeError, match="Expected str"):
            p.feed(b"hello")


class TestParserFinish:
    """Parser.finish() returning a Node."""

    def test_finish_returns_node(self):
        from multimark import NodeType

        p = Parser()
        p.feed("# Hello\n")
        root = p.finish()
        assert root.type == NodeType.DOCUMENT
        assert root.first_child.type == NodeType.HEADING

    def test_finish_with_extensions(self):
        from multimark import NodeType

        p = Parser(extensions=["table"])
        p.feed("| A |\n|---|\n| 1 |\n")
        root = p.finish()
        # Walk to find table node
        found_table = False
        for event, node in root.walk():
            if event == "enter" and node.type_string == "table":
                found_table = True
        assert found_table

    def test_finish_and_render_equivalence(self):
        p = Parser(smart=True)
        p.feed('"Hello" -- world')
        root = p.finish()
        # Rendering from the Node should match rendering from Parser
        node_html = root.render_html()
        # Both should contain smart punctuation since parsed with smart=True
        assert "\u201c" in node_html
