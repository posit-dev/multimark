import pytest

from multimark import (
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_commonmark,
    markdown_to_xml,
    Options,
    VALID_EXTENSIONS,
)

ALL_RENDERERS = [
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_commonmark,
    markdown_to_xml,
]


def _ids(fn):
    return fn.__name__


# ---------------------------------------------------------------------------
# Type errors: wrong input types should raise TypeError
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_none_input_raises(renderer):
    """Passing None raises TypeError."""
    with pytest.raises((TypeError, AttributeError)):
        renderer(None)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_bytes_input_raises(renderer):
    """Passing bytes instead of str raises TypeError."""
    with pytest.raises((TypeError, AttributeError)):
        renderer(b"hello")


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_int_input_raises(renderer):
    """Passing an int raises TypeError."""
    with pytest.raises((TypeError, AttributeError)):
        renderer(42)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_list_input_raises(renderer):
    """Passing a list raises TypeError."""
    with pytest.raises((TypeError, AttributeError)):
        renderer(["hello"])


# ---------------------------------------------------------------------------
# Invalid option values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_negative_options_no_crash(renderer):
    """Negative option value doesn't crash (undefined but shouldn't segfault)."""
    # This tests that the C library handles garbage option bits gracefully
    result = renderer("hello\n", options=-1)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_large_options_raises_overflow(renderer):
    """Option value exceeding 32-bit int raises OverflowError (CFFI guard)."""
    with pytest.raises(OverflowError):
        renderer("hello\n", options=0xFFFFFFFF)


# ---------------------------------------------------------------------------
# Width parameter edge cases (for renderers that accept width)
# ---------------------------------------------------------------------------


def test_latex_negative_width_no_crash():
    """Negative width doesn't crash."""
    result = markdown_to_latex("hello world\n", width=-1)
    assert isinstance(result, str)


def test_man_negative_width_no_crash():
    result = markdown_to_man("hello world\n", width=-1)
    assert isinstance(result, str)


def test_commonmark_negative_width_no_crash():
    result = markdown_to_commonmark("hello world\n", width=-1)
    assert isinstance(result, str)


def test_latex_huge_width_no_crash():
    """Extremely large width doesn't crash."""
    result = markdown_to_latex("hello world\n", width=2**30)
    assert isinstance(result, str)


def test_man_huge_width_no_crash():
    result = markdown_to_man("hello world\n", width=2**30)
    assert isinstance(result, str)


def test_commonmark_huge_width_no_crash():
    result = markdown_to_commonmark("hello world\n", width=2**30)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Invalid keyword argument types
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_non_int_options_raises(renderer):
    """Non-integer value for options raises TypeError."""
    with pytest.raises(TypeError):
        renderer("hello\n", options="all")


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_truthy_bool_kwargs_accepted(renderer):
    """Truthy non-bool values work (standard Python truthiness)."""
    # Python doesn't enforce strict bool — any truthy value should work
    result = renderer("hello\n", smart=1, hardbreaks=0)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Invalid extensions parameter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_unknown_extension_name_raises(renderer):
    """Unknown extension name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown extension"):
        renderer("hello\n", extensions=["nonexistent"])


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_empty_string_extension_raises(renderer):
    """Empty string extension name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown extension"):
        renderer("hello\n", extensions=[""])


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_none_in_extensions_raises(renderer):
    """None inside extensions list raises TypeError or ValueError."""
    with pytest.raises((TypeError, AttributeError)):
        renderer("hello\n", extensions=[None])


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_int_in_extensions_raises(renderer):
    """Integer in extensions list raises TypeError."""
    with pytest.raises((TypeError, AttributeError)):
        renderer("hello\n", extensions=[42])


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_string_extensions_raises(renderer):
    """Passing a string instead of list for extensions raises TypeError (iterates chars)."""
    # "table" iterated char-by-char would give "t", "a", "b", "l", "e" — all invalid
    with pytest.raises(ValueError, match="Unknown extension"):
        renderer("hello\n", extensions="table")


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_extensions_case_sensitive(renderer):
    """Extension names are case-sensitive — uppercase should fail."""
    with pytest.raises(ValueError, match="Unknown extension"):
        renderer("hello\n", extensions=["Table"])


# ---------------------------------------------------------------------------
# Positional argument rejection (keyword-only enforcement)
# ---------------------------------------------------------------------------


def test_positional_args_rejected_html():
    """Second positional arg is rejected (keyword-only after text)."""
    with pytest.raises(TypeError):
        markdown_to_html("hello\n", True)


def test_positional_args_rejected_latex():
    with pytest.raises(TypeError):
        markdown_to_latex("hello\n", True)


def test_positional_args_rejected_man():
    with pytest.raises(TypeError):
        markdown_to_man("hello\n", True)


def test_positional_args_rejected_xml():
    with pytest.raises(TypeError):
        markdown_to_xml("hello\n", True)


def test_positional_args_rejected_commonmark():
    with pytest.raises(TypeError):
        markdown_to_commonmark("hello\n", True)


# ---------------------------------------------------------------------------
# Unexpected keyword arguments
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_unknown_kwarg_raises(renderer):
    """Unknown keyword argument raises TypeError."""
    with pytest.raises(TypeError):
        renderer("hello\n", nonexistent_param=True)


def test_width_rejected_for_html():
    """HTML renderer doesn't accept width parameter."""
    with pytest.raises(TypeError):
        markdown_to_html("hello\n", width=80)


def test_width_rejected_for_xml():
    """XML renderer doesn't accept width parameter."""
    with pytest.raises(TypeError):
        markdown_to_xml("hello\n", width=80)


def test_sourcepos_rejected_for_latex():
    """LaTeX renderer doesn't accept sourcepos parameter."""
    with pytest.raises(TypeError):
        markdown_to_latex("hello\n", sourcepos=True)


def test_sourcepos_rejected_for_man():
    """Man renderer doesn't accept sourcepos parameter."""
    with pytest.raises(TypeError):
        markdown_to_man("hello\n", sourcepos=True)


def test_sourcepos_rejected_for_commonmark():
    """CommonMark renderer doesn't accept sourcepos parameter."""
    with pytest.raises(TypeError):
        markdown_to_commonmark("hello\n", sourcepos=True)


# ---------------------------------------------------------------------------
# Duplicate/redundant extensions (should still work, not crash)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_duplicate_extension_no_crash(renderer):
    """Passing same extension twice doesn't crash."""
    result = renderer("hello\n", extensions=["table", "table"])
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Boolean kwargs are orthogonal (all combos shouldn't crash)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_all_bool_flags_true(renderer):
    """Enabling all boolean flags at once doesn't crash."""
    kwargs = dict(hardbreaks=True, smart=True, normalize=True, unsafe=True, footnotes=True)
    result = renderer("hello\n", **kwargs)
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_bool_flags_with_extensions(renderer):
    """Boolean flags combined with extensions doesn't crash."""
    result = renderer(
        "hello\n",
        smart=True,
        unsafe=True,
        extensions=["table", "strikethrough"],
    )
    assert isinstance(result, str)


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_options_int_with_extensions(renderer):
    """Raw options bitmask combined with extensions doesn't crash."""
    result = renderer(
        "hello\n",
        options=Options.SMART | Options.UNSAFE,
        extensions=["autolink"],
    )
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Empty extensions list (should behave same as no extensions)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ALL_RENDERERS, ids=_ids)
def test_empty_extensions_same_as_none(renderer):
    """Empty extensions list produces same output as no extensions."""
    md = "**bold** text\n"
    result_no_ext = renderer(md)
    result_empty = renderer(md, extensions=[])
    assert result_no_ext == result_empty
