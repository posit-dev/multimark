import pytest
from click.testing import CliRunner

from multimark._cli import main
from multimark import __version__


@pytest.fixture
def runner():
    return CliRunner()


class TestBasicConversion:
    def test_stdin_to_html(self, runner):
        result = runner.invoke(main, input="# Hello\n")
        assert result.exit_code == 0
        assert "<h1>Hello</h1>" in result.output

    def test_file_argument(self, runner, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("**bold**\n")
        result = runner.invoke(main, [str(md_file)])
        assert result.exit_code == 0
        assert "<strong>bold</strong>" in result.output

    def test_output_to_file(self, runner, tmp_path):
        out_file = tmp_path / "out.html"
        result = runner.invoke(main, ["-o", str(out_file)], input="*italic*\n")
        assert result.exit_code == 0
        assert "<em>italic</em>" in out_file.read_text()


class TestOutputFormats:
    def test_html(self, runner):
        result = runner.invoke(main, ["--to", "html"], input="# Title\n")
        assert result.exit_code == 0
        assert "<h1>Title</h1>" in result.output

    def test_latex(self, runner):
        result = runner.invoke(main, ["--to", "latex"], input="# Title\n")
        assert result.exit_code == 0
        assert "\\section{Title}" in result.output

    def test_man(self, runner):
        result = runner.invoke(main, ["--to", "man"], input="# Title\n")
        assert result.exit_code == 0
        assert ".SH" in result.output

    def test_commonmark(self, runner):
        result = runner.invoke(main, ["--to", "commonmark"], input="*italic*\n")
        assert result.exit_code == 0
        assert "*italic*" in result.output

    def test_xml(self, runner):
        result = runner.invoke(main, ["--to", "xml"], input="hello\n")
        assert result.exit_code == 0
        assert "<?xml" in result.output
        assert "<text" in result.output


class TestOptions:
    def test_smart(self, runner):
        result = runner.invoke(main, ["--smart"], input='"Hello" -- world\n')
        assert result.exit_code == 0
        assert "\u201c" in result.output  # curly open quote
        assert "\u2013" in result.output  # en-dash

    def test_unsafe(self, runner):
        result = runner.invoke(main, ["--unsafe"], input="<div>raw</div>\n")
        assert result.exit_code == 0
        assert "<div>raw</div>" in result.output

    def test_safe_by_default(self, runner):
        result = runner.invoke(main, input="<script>alert('x')</script>\n")
        assert result.exit_code == 0
        assert "<script>" not in result.output

    def test_hardbreaks(self, runner):
        result = runner.invoke(main, ["--hardbreaks"], input="line1\nline2\n")
        assert result.exit_code == 0
        assert "<br />" in result.output

    def test_sourcepos_html(self, runner):
        result = runner.invoke(main, ["--sourcepos"], input="hello\n")
        assert result.exit_code == 0
        assert "data-sourcepos" in result.output

    def test_sourcepos_xml(self, runner):
        result = runner.invoke(main, ["--to", "xml", "--sourcepos"], input="hello\n")
        assert result.exit_code == 0
        assert 'sourcepos="' in result.output

    def test_sourcepos_ignored_for_latex(self, runner):
        result = runner.invoke(main, ["--to", "latex", "--sourcepos"], input="# Hi\n")
        assert result.exit_code == 0
        assert "\\section{Hi}" in result.output

    def test_footnotes(self, runner):
        md = "Text[^1]\n\n[^1]: A footnote.\n"
        result = runner.invoke(main, ["--footnotes"], input=md)
        assert result.exit_code == 0
        assert "footnote" in result.output.lower()


class TestExtensions:
    def test_table(self, runner):
        md = "| A | B |\n|---|---|\n| 1 | 2 |\n"
        result = runner.invoke(main, ["-e", "table"], input=md)
        assert result.exit_code == 0
        assert "<table>" in result.output

    def test_strikethrough(self, runner):
        result = runner.invoke(main, ["-e", "strikethrough"], input="~~del~~\n")
        assert result.exit_code == 0
        assert "<del>del</del>" in result.output

    def test_autolink(self, runner):
        result = runner.invoke(main, ["-e", "autolink"], input="Visit https://example.com\n")
        assert result.exit_code == 0
        assert 'href="https://example.com"' in result.output

    def test_multiple_extensions(self, runner):
        md = "~~del~~\n\n| A |\n|---|\n| 1 |\n"
        result = runner.invoke(main, ["-e", "strikethrough", "-e", "table"], input=md)
        assert result.exit_code == 0
        assert "<del>" in result.output
        assert "<table>" in result.output


class TestMetadata:
    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Convert CommonMark/GFM" in result.output
        assert "--to" in result.output


class TestWidth:
    def test_width_latex(self, runner):
        long_text = "word " * 50 + "\n"
        result = runner.invoke(main, ["--to", "latex", "--width", "40"], input=long_text)
        assert result.exit_code == 0
        content_lines = [l for l in result.output.split("\n") if "word" in l]
        assert all(len(l) <= 40 for l in content_lines)

    def test_width_man(self, runner):
        long_text = "word " * 50 + "\n"
        result = runner.invoke(main, ["--to", "man", "--width", "60"], input=long_text)
        assert result.exit_code == 0
        content_lines = [l for l in result.output.split("\n") if "word" in l]
        assert all(len(l) <= 60 for l in content_lines)

    def test_width_commonmark(self, runner):
        long_text = "word " * 50 + "\n"
        result = runner.invoke(main, ["--to", "commonmark", "--width", "72"], input=long_text)
        assert result.exit_code == 0
        content_lines = [l for l in result.output.split("\n") if "word" in l]
        assert all(len(l) <= 72 for l in content_lines)

    def test_width_ignored_for_html(self, runner):
        result = runner.invoke(main, ["--to", "html", "--width", "40"], input="hello\n")
        assert result.exit_code == 0
        assert "<p>hello</p>" in result.output

    def test_width_default_no_wrap(self, runner):
        long_text = "word " * 50 + "\n"
        result = runner.invoke(main, ["--to", "latex"], input=long_text)
        assert result.exit_code == 0
        content_lines = [l for l in result.output.split("\n") if "word" in l]
        assert any(len(l) > 80 for l in content_lines)
