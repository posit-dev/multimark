from enum import IntFlag
from importlib.metadata import PackageNotFoundError, version as _get_version

try:
    __version__ = _get_version("multimark")
except PackageNotFoundError:
    __version__ = "0.0.0"

from multimark._cmark import (
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_commonmark,
    markdown_to_xml,
    cmark_version,
    VALID_EXTENSIONS,
)
from multimark._parser import Parser
from multimark._node import Node, NodeType, ListType, DelimType, parse
from multimark._binding import lib


class Options(IntFlag):
    """CommonMark/GFM parsing and rendering options.

    An `IntFlag` enumeration of all option flags supported by the cmark-gfm library.
    Options can be combined using the bitwise OR operator (`|`) and passed to any
    renderer's `options=` parameter. This provides a composable, lower-level alternative
    to the named boolean keyword arguments available on each renderer function.

    Most users will prefer the named keyword arguments (e.g., `smart=True`) for common
    options. The `Options` bitmask is useful when you need to combine multiple flags
    into a single reusable value, or when working with GFM-specific flags that do not
    have dedicated keyword arguments.

    Examples
    --------
    Combine multiple flags with the `|` operator:

    ```{python}
    from multimark import markdown_to_html, Options

    opts = Options.SMART | Options.UNSAFE
    markdown_to_html('"Hello" -- world', options=opts)
    ```

    Mix a bitmask with named keyword arguments (they are OR'd together):

    ```{python}
    text = "Here's some *text* to convert"
    markdown_to_html(text, options=Options.SMART, footnotes=True)
    ```

    Use GFM-specific flags that have no keyword shortcut:

    ```{python}
    markdown_to_html(
        "~~deleted~~",
        options=Options.STRIKETHROUGH_DOUBLE_TILDE,
        extensions=["strikethrough"],
    )
    ```
    """

    DEFAULT = lib.CMARK_OPT_DEFAULT
    SOURCEPOS = lib.CMARK_OPT_SOURCEPOS
    HARDBREAKS = lib.CMARK_OPT_HARDBREAKS
    SAFE = lib.CMARK_OPT_SAFE
    UNSAFE = lib.CMARK_OPT_UNSAFE
    NOBREAKS = lib.CMARK_OPT_NOBREAKS
    NORMALIZE = lib.CMARK_OPT_NORMALIZE
    VALIDATE_UTF8 = lib.CMARK_OPT_VALIDATE_UTF8
    SMART = lib.CMARK_OPT_SMART
    # GFM-specific options
    GITHUB_PRE_LANG = lib.CMARK_OPT_GITHUB_PRE_LANG
    LIBERAL_HTML_TAG = lib.CMARK_OPT_LIBERAL_HTML_TAG
    FOOTNOTES = lib.CMARK_OPT_FOOTNOTES
    STRIKETHROUGH_DOUBLE_TILDE = lib.CMARK_OPT_STRIKETHROUGH_DOUBLE_TILDE
    TABLE_PREFER_STYLE_ATTRIBUTES = lib.CMARK_OPT_TABLE_PREFER_STYLE_ATTRIBUTES
    FULL_INFO_STRING = lib.CMARK_OPT_FULL_INFO_STRING


__all__ = [
    "markdown_to_html",
    "markdown_to_latex",
    "markdown_to_man",
    "markdown_to_commonmark",
    "markdown_to_xml",
    "cmark_version",
    "Options",
    "Parser",
    "parse",
    "Node",
    "NodeType",
    "ListType",
    "DelimType",
    "VALID_EXTENSIONS",
    "__version__",
]
