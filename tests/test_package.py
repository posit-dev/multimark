from multimark import (
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_commonmark,
    markdown_to_xml,
    cmark_version,
    Options,
    __version__,
)


def test_cmark_version_string():
    """cmark_version() returns a version string like '0.29.0.gfm.13'."""
    v = cmark_version()
    assert "gfm" in v
    parts = v.split(".")
    assert len(parts) == 5  # major.minor.patch.gfm.release
    assert parts[0].isdigit()
    assert parts[3] == "gfm"


def test_package_version_available():
    """__version__ is set (not the fallback)."""
    assert __version__ != "0.0.0"
    assert isinstance(__version__, str)


def test_all_renderers_return_str():
    """All renderers return str type."""
    md = "Hello\n"
    assert isinstance(markdown_to_html(md), str)
    assert isinstance(markdown_to_latex(md), str)
    assert isinstance(markdown_to_man(md), str)
    assert isinstance(markdown_to_commonmark(md), str)
    assert isinstance(markdown_to_xml(md), str)


def test_options_is_intflag():
    """Options members can be combined with bitwise OR."""
    combined = Options.SMART | Options.SOURCEPOS
    assert isinstance(combined, int)
    assert combined & Options.SMART
    assert combined & Options.SOURCEPOS


def test_options_default_is_zero():
    assert Options.DEFAULT == 0
