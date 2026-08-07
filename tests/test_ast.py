import pytest

from multimark import parse, Node, NodeType, ListType, DelimType, Options


class TestParse:
    """Tests for the parse() function."""

    def test_basic_parse(self):
        doc = parse("hello")
        assert doc.type == NodeType.DOCUMENT

    def test_empty_string(self):
        doc = parse("")
        assert doc.type == NodeType.DOCUMENT
        assert doc.first_child is None

    def test_parse_type_error(self):
        with pytest.raises(TypeError, match="Expected str"):
            parse(123)

    def test_parse_bytes_type_error(self):
        with pytest.raises(TypeError, match="Expected str"):
            parse(b"hello")

    def test_parse_with_extensions(self):
        doc = parse("| A |\n|---|\n| 1 |\n", extensions=["table"])
        found_table = False
        for event, node in doc.walk():
            if event == "enter" and node.type_string == "table":
                found_table = True
        assert found_table

    def test_parse_invalid_extension(self):
        with pytest.raises(ValueError, match="Unknown extension"):
            parse("hello", extensions=["bogus"])

    def test_parse_smart(self):
        doc = parse('"Hello"', smart=True)
        for event, node in doc.walk():
            if node.type == NodeType.TEXT:
                assert "\u201c" in node.literal
                break

    def test_parse_with_options_bitmask(self):
        doc = parse("# Hello\n", options=int(Options.SMART))
        assert doc.type == NodeType.DOCUMENT


class TestNodeType:
    """Tests for NodeType enum."""

    def test_block_types(self):
        assert NodeType.DOCUMENT is not None
        assert NodeType.PARAGRAPH is not None
        assert NodeType.HEADING is not None
        assert NodeType.BLOCK_QUOTE is not None
        assert NodeType.LIST is not None
        assert NodeType.ITEM is not None
        assert NodeType.CODE_BLOCK is not None
        assert NodeType.THEMATIC_BREAK is not None

    def test_inline_types(self):
        assert NodeType.TEXT is not None
        assert NodeType.EMPH is not None
        assert NodeType.STRONG is not None
        assert NodeType.LINK is not None
        assert NodeType.IMAGE is not None
        assert NodeType.CODE is not None
        assert NodeType.SOFTBREAK is not None
        assert NodeType.LINEBREAK is not None

    def test_html_types(self):
        assert NodeType.HTML_BLOCK is not None
        assert NodeType.HTML_INLINE is not None

    def test_node_type_values_are_ints(self):
        assert isinstance(NodeType.DOCUMENT.value, int)
        assert isinstance(NodeType.TEXT.value, int)


class TestNodeTraversal:
    """Tests for tree traversal properties."""

    def test_first_child(self):
        doc = parse("# Hello\n\nWorld\n")
        heading = doc.first_child
        assert heading.type == NodeType.HEADING

    def test_last_child(self):
        doc = parse("# Hello\n\nWorld\n")
        para = doc.last_child
        assert para.type == NodeType.PARAGRAPH

    def test_next_sibling(self):
        doc = parse("# Hello\n\nWorld\n")
        heading = doc.first_child
        para = heading.next
        assert para.type == NodeType.PARAGRAPH

    def test_previous_sibling(self):
        doc = parse("# Hello\n\nWorld\n")
        para = doc.last_child
        heading = para.previous
        assert heading.type == NodeType.HEADING

    def test_parent(self):
        doc = parse("**bold**")
        para = doc.first_child
        assert para.parent is doc

    def test_parent_of_root_is_none(self):
        doc = parse("hello")
        assert doc.parent is None

    def test_next_of_last_is_none(self):
        doc = parse("hello")
        last = doc.last_child
        assert last.next is None

    def test_previous_of_first_is_none(self):
        doc = parse("hello")
        first = doc.first_child
        assert first.previous is None

    def test_children_iterator(self):
        doc = parse("# One\n\nTwo\n\nThree\n")
        children = list(doc.children)
        assert len(children) == 3
        assert children[0].type == NodeType.HEADING
        assert children[1].type == NodeType.PARAGRAPH
        assert children[2].type == NodeType.PARAGRAPH

    def test_children_of_leaf(self):
        doc = parse("hello")
        text_node = doc.first_child.first_child  # paragraph > text
        children = list(text_node.children)
        assert children == []

    def test_node_identity(self):
        doc = parse("hello")
        assert doc.first_child is doc.first_child


class TestNodeWalk:
    """Tests for the walk() iterator."""

    def test_walk_events(self):
        doc = parse("**bold**")
        events = list(doc.walk())
        # Should have enter/exit pairs for container nodes
        event_types = [e for e, _ in events]
        assert "enter" in event_types
        assert "exit" in event_types

    def test_walk_enter_exit_pairs(self):
        doc = parse("**bold**")
        enters = [(e, n.type_string) for e, n in doc.walk() if e == "enter"]
        exits = [(e, n.type_string) for e, n in doc.walk() if e == "exit"]
        # Container nodes should have matching enter/exit
        enter_types = [t for _, t in enters]
        exit_types = [t for _, t in exits]
        assert "document" in enter_types
        assert "document" in exit_types

    def test_walk_text_only_enter(self):
        doc = parse("hello")
        for event, node in doc.walk():
            if node.type == NodeType.TEXT:
                assert event == "enter"

    def test_walk_heading(self):
        doc = parse("# Hello\n")
        found = False
        for event, node in doc.walk():
            if event == "enter" and node.type == NodeType.HEADING:
                assert node.heading_level == 1
                found = True
        assert found

    def test_walk_link(self):
        doc = parse("[text](http://example.com)\n")
        found = False
        for event, node in doc.walk():
            if event == "enter" and node.type == NodeType.LINK:
                assert node.url == "http://example.com"
                found = True
        assert found

    def test_walk_collect_all_text(self):
        doc = parse("Hello **world** end")
        texts = []
        for event, node in doc.walk():
            if event == "enter" and node.type == NodeType.TEXT:
                texts.append(node.literal)
        assert texts == ["Hello ", "world", " end"]


class TestNodeProperties:
    """Tests for node property accessors."""

    def test_heading_level(self):
        for level in range(1, 7):
            doc = parse(f"{'#' * level} Heading\n")
            h = doc.first_child
            assert h.heading_level == level

    def test_literal_text(self):
        doc = parse("hello world")
        text_node = doc.first_child.first_child
        assert text_node.literal == "hello world"

    def test_literal_code(self):
        doc = parse("`code`")
        for event, node in doc.walk():
            if node.type == NodeType.CODE:
                assert node.literal == "code"

    def test_literal_none_for_containers(self):
        doc = parse("hello")
        assert doc.literal is None  # DOCUMENT has no literal

    def test_url_link(self):
        doc = parse("[text](http://example.com)\n")
        for event, node in doc.walk():
            if node.type == NodeType.LINK:
                assert node.url == "http://example.com"
                break

    def test_title_link(self):
        doc = parse('[text](http://x.com "My Title")\n')
        for event, node in doc.walk():
            if node.type == NodeType.LINK:
                assert node.title == "My Title"
                break

    def test_url_image(self):
        doc = parse("![alt](http://img.com/photo.png)\n")
        for event, node in doc.walk():
            if node.type == NodeType.IMAGE:
                assert node.url == "http://img.com/photo.png"
                break

    def test_list_type_bullet(self):
        doc = parse("- one\n- two\n")
        for event, node in doc.walk():
            if node.type == NodeType.LIST:
                assert node.list_type == ListType.BULLET
                break

    def test_list_type_ordered(self):
        doc = parse("1. one\n2. two\n")
        for event, node in doc.walk():
            if node.type == NodeType.LIST:
                assert node.list_type == ListType.ORDERED
                assert node.list_start == 1
                break

    def test_list_start_nonone(self):
        doc = parse("3. three\n4. four\n")
        for event, node in doc.walk():
            if node.type == NodeType.LIST:
                assert node.list_start == 3
                break

    def test_list_tight(self):
        doc = parse("- one\n- two\n")
        for event, node in doc.walk():
            if node.type == NodeType.LIST:
                assert node.list_tight is True
                break

    def test_list_loose(self):
        doc = parse("- one\n\n- two\n")
        for event, node in doc.walk():
            if node.type == NodeType.LIST:
                assert node.list_tight is False
                break

    def test_fence_info(self):
        doc = parse("```python\ncode\n```\n")
        for event, node in doc.walk():
            if node.type == NodeType.CODE_BLOCK:
                assert node.fence_info == "python"
                break

    def test_fence_info_empty(self):
        doc = parse("```\ncode\n```\n")
        for event, node in doc.walk():
            if node.type == NodeType.CODE_BLOCK:
                assert node.fence_info == ""
                break

    def test_type_string(self):
        doc = parse("hello")
        assert doc.type_string == "document"
        assert doc.first_child.type_string == "paragraph"


class TestNodeSourcepos:
    """Tests for source position properties."""

    def test_heading_sourcepos(self):
        doc = parse("# Hello\n", options=int(Options.SOURCEPOS))
        h = doc.first_child
        assert h.start_line == 1
        assert h.start_column == 1
        assert h.end_line == 1

    def test_multiline_sourcepos(self):
        doc = parse("# H1\n\npara\n", options=int(Options.SOURCEPOS))
        para = doc.last_child
        assert para.start_line == 3

    def test_sourcepos_zero_without_flag(self):
        # Without SOURCEPOS option, positions should still be available
        # (cmark always tracks them; the option controls HTML output)
        doc = parse("# Hello\n")
        h = doc.first_child
        assert h.start_line == 1


class TestNodeRendering:
    """Tests for rendering from Node."""

    def test_render_html(self):
        doc = parse("**bold**")
        assert doc.render_html() == "<p><strong>bold</strong></p>\n"

    def test_render_html_unsafe(self):
        doc = parse("<div>raw</div>", unsafe=True)
        html = doc.render_html(unsafe=True)
        assert "<div>raw</div>" in html

    def test_render_html_sourcepos(self):
        doc = parse("hello")
        html = doc.render_html(sourcepos=True)
        assert "data-sourcepos" in html

    def test_render_xml(self):
        doc = parse("**bold**")
        xml = doc.render_xml()
        assert "<?xml" in xml
        assert "<strong>" in xml

    def test_render_latex(self):
        doc = parse("**bold**")
        latex = doc.render_latex()
        assert "\\textbf{bold}" in latex

    def test_render_man(self):
        doc = parse("**bold**")
        man = doc.render_man()
        assert "\\f[B]bold\\f[]" in man

    def test_render_commonmark(self):
        doc = parse("*italic*")
        cm = doc.render_commonmark()
        assert "*italic*" in cm

    def test_render_subtree(self):
        doc = parse("# Heading\n\nParagraph\n")
        para = doc.last_child
        html = para.render_html()
        assert "<p>Paragraph</p>" in html
        assert "<h1>" not in html


class TestNodeMutation:
    """Tests for AST mutation."""

    def test_set_literal(self):
        doc = parse("hello")
        text_node = doc.first_child.first_child
        text_node.literal = "goodbye"
        assert "goodbye" in doc.render_html()
        assert "hello" not in doc.render_html()

    def test_set_url(self):
        doc = parse("[text](http://old.com)\n")
        for _, node in doc.walk():
            if node.type == NodeType.LINK:
                node.url = "http://new.com"
                break
        assert "http://new.com" in doc.render_html()

    def test_set_title(self):
        doc = parse('[text](http://x.com "old")\n')
        for _, node in doc.walk():
            if node.type == NodeType.LINK:
                node.title = "new title"
                break
        # Title appears in rendered HTML
        assert "new title" in doc.render_html()

    def test_set_heading_level(self):
        doc = parse("# H1\n")
        h = doc.first_child
        h.heading_level = 3
        assert "<h3>" in doc.render_html()

    def test_set_list_type(self):
        doc = parse("- one\n- two\n")
        for _, node in doc.walk():
            if node.type == NodeType.LIST:
                node.list_type = ListType.ORDERED
                node.list_start = 1
                break
        html = doc.render_html()
        assert "<ol>" in html

    def test_set_list_start(self):
        doc = parse("1. one\n2. two\n")
        for _, node in doc.walk():
            if node.type == NodeType.LIST:
                node.list_start = 5
                break
        html = doc.render_html()
        assert 'start="5"' in html

    def test_set_list_tight(self):
        doc = parse("- one\n- two\n")
        for _, node in doc.walk():
            if node.type == NodeType.LIST:
                node.list_tight = False
                break
        # Loose lists have <p> inside items
        html = doc.render_html()
        assert "<p>" in html

    def test_set_fence_info(self):
        doc = parse("```\ncode\n```\n")
        for _, node in doc.walk():
            if node.type == NodeType.CODE_BLOCK:
                node.fence_info = "python"
                break
        html = doc.render_html()
        assert "python" in html

    def test_unlink(self):
        doc = parse("# Heading\n\nPara\n")
        heading = doc.first_child
        heading.unlink()
        html = doc.render_html()
        assert "<h1>" not in html
        assert "<p>Para</p>" in html

    def test_append_child(self):
        doc = parse("hello\n")
        new_para = Node.new(NodeType.PARAGRAPH)
        new_text = Node.new(NodeType.TEXT)
        new_text.literal = "appended"
        new_para.append_child(new_text)
        doc.append_child(new_para)
        html = doc.render_html()
        assert "appended" in html

    def test_prepend_child(self):
        doc = parse("hello\n")
        heading = Node.new(NodeType.HEADING)
        heading.heading_level = 1
        text = Node.new(NodeType.TEXT)
        text.literal = "Title"
        heading.append_child(text)
        doc.prepend_child(heading)
        html = doc.render_html()
        assert html.startswith("<h1>Title</h1>\n<p>hello</p>")

    def test_insert_before(self):
        doc = parse("# H1\n\nParagraph\n")
        para = doc.last_child
        new_para = Node.new(NodeType.PARAGRAPH)
        text = Node.new(NodeType.TEXT)
        text.literal = "inserted"
        new_para.append_child(text)
        para.insert_before(new_para)
        html = doc.render_html()
        # "inserted" should come before "Paragraph"
        assert html.index("inserted") < html.index("Paragraph")

    def test_insert_after(self):
        doc = parse("# H1\n\nParagraph\n")
        heading = doc.first_child
        new_para = Node.new(NodeType.PARAGRAPH)
        text = Node.new(NodeType.TEXT)
        text.literal = "after heading"
        new_para.append_child(text)
        heading.insert_after(new_para)
        html = doc.render_html()
        assert html.index("after heading") < html.index("Paragraph")

    def test_replace(self):
        doc = parse("# Old\n\nPara\n")
        heading = doc.first_child
        new_heading = Node.new(NodeType.HEADING)
        new_heading.heading_level = 2
        text = Node.new(NodeType.TEXT)
        text.literal = "New"
        new_heading.append_child(text)
        heading.replace(new_heading)
        html = doc.render_html()
        assert "<h2>New</h2>" in html
        assert "<h1>" not in html


class TestNodeNew:
    """Tests for Node.new() factory."""

    def test_new_text(self):
        n = Node.new(NodeType.TEXT)
        assert n.type == NodeType.TEXT
        n.literal = "hello"
        assert n.literal == "hello"

    def test_new_heading(self):
        n = Node.new(NodeType.HEADING)
        n.heading_level = 3
        assert n.heading_level == 3

    def test_new_paragraph(self):
        n = Node.new(NodeType.PARAGRAPH)
        assert n.type == NodeType.PARAGRAPH

    def test_new_link(self):
        n = Node.new(NodeType.LINK)
        n.url = "http://example.com"
        n.title = "Example"
        assert n.url == "http://example.com"
        assert n.title == "Example"

    def test_new_code_block(self):
        n = Node.new(NodeType.CODE_BLOCK)
        n.literal = "print('hello')"
        n.fence_info = "python"
        assert n.literal == "print('hello')"
        assert n.fence_info == "python"

    def test_new_list(self):
        n = Node.new(NodeType.LIST)
        n.list_type = ListType.ORDERED
        n.list_start = 1
        assert n.list_type == ListType.ORDERED


class TestNodeRepr:
    """Tests for Node.__repr__."""

    def test_document_repr(self):
        doc = parse("hello")
        assert "document" in repr(doc)

    def test_heading_repr(self):
        doc = parse("# Hello\n")
        h = doc.first_child
        assert "heading" in repr(h)
        assert "level=1" in repr(h)

    def test_text_repr(self):
        doc = parse("hello world")
        text = doc.first_child.first_child
        r = repr(text)
        assert "text" in r
        assert "hello" in r

    def test_link_repr(self):
        doc = parse("[t](http://x.com)\n")
        for _, node in doc.walk():
            if node.type == NodeType.LINK:
                assert "http://x.com" in repr(node)
                break

    def test_long_text_truncated(self):
        doc = parse("a" * 100)
        text = doc.first_child.first_child
        r = repr(text)
        assert "..." in r
        assert len(r) < 100


class TestNodeEquality:
    """Tests for Node equality and hashing."""

    def test_same_node_equal(self):
        doc = parse("hello")
        assert doc.first_child == doc.first_child

    def test_different_nodes_not_equal(self):
        doc = parse("# A\n\nB\n")
        assert doc.first_child != doc.last_child

    def test_node_hashable(self):
        doc = parse("hello")
        s = {doc, doc.first_child}
        assert len(s) == 2

    def test_identity_preserved(self):
        doc = parse("hello")
        a = doc.first_child
        b = doc.first_child
        assert a is b


class TestNodeErrors:
    """Tests for error handling in Node operations."""

    def test_set_literal_type_error(self):
        doc = parse("hello")
        text = doc.first_child.first_child
        with pytest.raises(TypeError):
            text.literal = 123

    def test_set_url_type_error(self):
        doc = parse("[t](http://x.com)\n")
        for _, node in doc.walk():
            if node.type == NodeType.LINK:
                with pytest.raises(TypeError):
                    node.url = 123
                break

    def test_set_heading_level_on_non_heading(self):
        doc = parse("hello")
        para = doc.first_child
        with pytest.raises(ValueError):
            para.heading_level = 1

    def test_set_literal_on_container(self):
        doc = parse("hello")
        with pytest.raises(ValueError):
            doc.literal = "text"
