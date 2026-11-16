import pytest
from click.testing import CliRunner

from multimark import (
    Parser,
    markdown_to_commonmark,
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_plaintext,
    markdown_to_xml,
    parse,
)
from multimark._cli import main

MATH = ["math"]


def _math_spans(md, extensions=MATH):
    """(kind, tex) for each math node in the parsed document."""
    root = parse(md, extensions=extensions)
    return [
        ("display" if node.math_display else "inline", node.first_child.literal)
        for event, node in root.walk()
        if event == "enter" and node.type_string == "math"
    ]


# Expected spans come from pandoc 3.14 (`-f markdown`, whose
# `tex_math_dollars` rules the extension follows).
PANDOC_CASES = [
    ("$x^2$", [("inline", "x^2")]),
    ("$$\\int f$$", [("display", "\\int f")]),
    # Inline math can't open before or close after whitespace, or close
    # before a digit, so prices stay text.
    ("$5 and $10", []),
    ("price: $3.50 or $4", []),
    ("$ a$", []),
    ("$a $", []),
    ("$a$5", []),
    ("$a$b", [("inline", "a")]),
    ("a$b$c", [("inline", "b")]),
    ("$[0, 1]$", [("inline", "[0, 1]")]),
    # Display math may have whitespace inside its delimiters; it's trimmed.
    ("$$ x $$", [("display", "x")]),
    ("$$\na\n$$", [("display", "a")]),
    ("$$a$$5", [("display", "a")]),
    ("$$$$", []),
    # A backslash escapes the next character.
    ("$a\\$b$", [("inline", "a\\$b")]),
    ("$$a\\$$b$$", [("display", "a\\$$b")]),
    ("$x\\$", []),
    ("\\$x$", []),
    ("$\\}$", [("inline", "\\}")]),
    # A control space at the end survives trimming.
    ("$a\\ $", [("inline", "a\\ ")]),
    # Groups and comments are consumed whole.
    ("$\\text{$x$}$ y", [("inline", "\\text{$x$}")]),
    ("${a$}$", [("inline", "{a$}")]),
    ("$a{b$", []),
    ("$a % c $\nb$", [("inline", "a % c $\nb")]),
    # Math can't span a blank line, and an inline closer can't start a line.
    ("$a\n\nb$", []),
    ("$$a\n\nb$$", []),
    ("$a\n$", []),
    ("$a  \nb$", [("inline", "a  \nb")]),
    # When `$$` doesn't open display math, the first `$` is literal.
    ("$$x$", [("inline", "x")]),
    ("$x$$", [("inline", "x")]),
    ("$a$$b$", [("inline", "a"), ("inline", "b")]),
    # Interaction with other inlines.
    ("`$x$` and $y$", [("inline", "y")]),
    ("[$x$](u)", [("inline", "x")]),
    ("*a $b* c$", [("inline", "b* c")]),
]


@pytest.mark.parametrize("md, expected", PANDOC_CASES, ids=[c[0] for c in PANDOC_CASES])
def test_matches_pandoc(md, expected):
    """Math spans agree with pandoc's tex_math_dollars."""
    assert _math_spans(md) == expected


def test_crlf_normalized():
    assert _math_spans("$$a\r\nb$$") == [("display", "a\nb")]


def test_disabled_by_default():
    md = "$x$ and $$y$$\n"
    assert markdown_to_html(md) == "<p>$x$ and $$y$$</p>\n"
    assert _math_spans(md, extensions=[]) == []


class TestRenderers:
    MD = "Let $a<b$ and $$\\sum_i x_i$$ cost $5.\n"

    def test_html(self):
        assert markdown_to_html(self.MD, extensions=MATH) == (
            '<p>Let <span class="math inline">\\(a&lt;b\\)</span> and '
            '<span class="math display">\\[\\sum_i x_i\\]</span> cost $5.</p>\n'
        )

    def test_html_escapes_quotes(self):
        assert markdown_to_html('$a"b$', extensions=MATH) == (
            '<p><span class="math inline">\\(a&quot;b\\)</span></p>\n'
        )

    def test_html_keeps_tex_verbatim(self):
        # No smart punctuation, entities, or emphasis inside the TeX.
        md = "$a -- b's *c* &amp; d$"
        assert markdown_to_html(md, extensions=MATH, smart=True) == (
            '<p><span class="math inline">\\(a -- b\'s *c* &amp;amp; d\\)</span></p>\n'
        )

    def test_latex(self):
        assert markdown_to_latex(self.MD, extensions=MATH) == (
            "Let \\(a<b\\) and \\[\\sum_i x_i\\] cost \\$5.\n"
        )

    def test_latex_display_math_inline_in_table_cell(self):
        # `\[...\]` isn't allowed in a tabular cell, so it's set inline (as in Pandoc).
        md = "| a | b |\n|---|---|\n| $$x$$ | **$$y$$** |\n"
        out = markdown_to_latex(md, extensions=["math", "table"])
        assert "\\(x\\) & \\textbf{\\(y\\)} \\\\" in out
        assert "\\[" not in out

    def test_man(self):
        assert markdown_to_man(self.MD, extensions=MATH) == (
            ".PP\nLet $a<b$ and $$\\esum_i x_i$$ cost $5.\n"
        )

    def test_commonmark(self):
        assert markdown_to_commonmark(self.MD, extensions=MATH) == (
            "Let $a<b$ and $$\\sum_i x_i$$ cost \\$5.\n"
        )

    def test_plaintext(self):
        assert markdown_to_plaintext(self.MD, extensions=MATH) == (
            "Let $a<b$ and $$\\sum_i x_i$$ cost $5.\n"
        )

    def test_xml(self):
        xml = markdown_to_xml("$a<b$ $$c$$", extensions=MATH)
        assert (
            '<math type="inline">\n'
            '      <text xml:space="preserve">a&lt;b</text>\n'
            "    </math>"
        ) in xml
        assert '<math type="display">' in xml

    def test_parser_render_html(self):
        with Parser(extensions=MATH) as p:
            p.feed("$x")
            p.feed("^2$\n")
            assert p.render_html() == '<p><span class="math inline">\\(x^2\\)</span></p>\n'

    def test_wrapping_does_not_break_tex(self):
        md = "word " * 12 + "$a + b + c$ " + "word " * 5
        out = markdown_to_commonmark(md, extensions=MATH, width=40)
        assert "$a + b + c$" in out


class TestCommonMarkRoundTrip:
    @pytest.mark.parametrize(
        "md",
        [
            "Let $a<b$ and $$\\sum_{i=1}^n x_i$$ cost \\$5 or $5.\n",
            "$$\n\\begin{aligned}\na &= b \\\\\nc &= d\n\\end{aligned}\n$$\n",
            "> quote $$a\n> b$$ end\n",
            "- item $x$\n- $$y\n  z$$\n",
            "$\\text{$x$}$ and *$a$* and [$b$](u)\n",
        ],
    )
    def test_round_trip(self, md):
        cm = markdown_to_commonmark(md, extensions=MATH)
        assert markdown_to_html(cm, extensions=MATH) == markdown_to_html(md, extensions=MATH)

    def test_literal_dollars_escaped(self):
        assert markdown_to_commonmark("$5 and $x$", extensions=MATH) == "\\$5 and $x$\n"

    def test_dollars_not_escaped_without_math(self):
        assert markdown_to_commonmark("$5 and $x$", extensions=["table"]) == "$5 and $x$\n"


class TestNode:
    def test_math_node(self):
        root = parse("a $x$ $$y$$", extensions=MATH)
        para = root.first_child
        inline = para.first_child.next
        display = inline.next.next
        assert inline.type_string == "math"
        assert inline.math_display is False
        assert display.math_display is True
        assert inline.first_child.type_string == "text"
        assert inline.first_child.literal == "x"
        assert inline.first_child.next is None

    def test_math_display_false_for_other_nodes(self):
        root = parse("$$y$$", extensions=MATH)
        assert root.math_display is False
        assert root.first_child.first_child.first_child.math_display is False


class TestSourcepos:
    def test_positions(self):
        xml = markdown_to_xml("a $x$\nb $$y\nz$$ c", extensions=MATH, sourcepos=True)
        assert '<math sourcepos="1:3-1:5" type="inline">' in xml
        assert '<text sourcepos="1:4-1:4" xml:space="preserve">x</text>' in xml
        assert '<math sourcepos="2:3-3:3" type="display">' in xml
        # Text after multi-line math is on the right line and column.
        assert '<text sourcepos="3:4-3:5" xml:space="preserve"> c</text>' in xml

    def test_html_sourcepos(self):
        html = markdown_to_html("$x$", extensions=MATH, sourcepos=True)
        assert html == (
            '<p data-sourcepos="1:1-1:3"><span class="math inline">\\(x\\)</span></p>\n'
        )


class TestOtherExtensions:
    def test_autolink_skips_tex(self):
        html = markdown_to_html(
            "$a@b.com$ and $www.x.com$ but www.y.com", extensions=["math", "autolink"]
        )
        assert html == (
            '<p><span class="math inline">\\(a@b.com\\)</span> and '
            '<span class="math inline">\\(www.x.com\\)</span> but '
            '<a href="http://www.y.com">www.y.com</a></p>\n'
        )

    def test_strikethrough(self):
        html = markdown_to_html("~~$x$~~ $~~y~~$", extensions=["math", "strikethrough"])
        assert html == (
            '<p><del><span class="math inline">\\(x\\)</span></del> '
            '<span class="math inline">\\(~~y~~\\)</span></p>\n'
        )

    def test_table_cells(self):
        md = "| a | b |\n|---|---|\n| $x$ | $$y$$ |\n"
        html = markdown_to_html(md, extensions=["math", "table"])
        assert '<td><span class="math inline">\\(x\\)</span></td>' in html
        assert '<td><span class="math display">\\[y\\]</span></td>' in html

    def test_heading_and_emphasis(self):
        html = markdown_to_html("# $x$ **$y$**", extensions=MATH)
        assert html == (
            '<h1><span class="math inline">\\(x\\)</span> '
            '<strong><span class="math inline">\\(y\\)</span></strong></h1>\n'
        )


def test_cli():
    result = CliRunner().invoke(main, ["-e", "math"], input="$x$\n")
    assert result.exit_code == 0
    assert '<span class="math inline">\\(x\\)</span>' in result.output

