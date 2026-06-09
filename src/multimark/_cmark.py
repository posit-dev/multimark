from __future__ import annotations

from typing import Sequence

from multimark._binding import ffi, lib

# Register all built-in GFM extensions once at import time.
lib.cmark_gfm_core_extensions_ensure_registered()

# Valid extension names recognized by cmark-gfm.
VALID_EXTENSIONS = frozenset(
    ["table", "strikethrough", "autolink", "tagfilter", "tasklist"]
)

# Cache resolved extension pointers to avoid repeated C lookups.
_EXT_CACHE: dict[str, object] = {}


def _get_extension(name: str):
    """Return the cached C pointer for a named extension."""
    try:
        return _EXT_CACHE[name]
    except KeyError:
        ext = lib.cmark_find_syntax_extension(name.encode("utf-8"))
        if ext == ffi.NULL:
            raise ValueError(f"Unknown extension: {name!r}")
        _EXT_CACHE[name] = ext
        return ext


def _build_options(
    options: int,
    hardbreaks: bool,
    smart: bool,
    normalize: bool,
    sourcepos: bool,
    unsafe: bool,
    footnotes: bool,
) -> int:
    """Combine named boolean flags with a raw options bitmask."""
    if hardbreaks:
        options |= lib.CMARK_OPT_HARDBREAKS
    if smart:
        options |= lib.CMARK_OPT_SMART
    if normalize:
        options |= lib.CMARK_OPT_NORMALIZE
    if sourcepos:
        options |= lib.CMARK_OPT_SOURCEPOS
    if unsafe:
        options |= lib.CMARK_OPT_UNSAFE
    if footnotes:
        options |= lib.CMARK_OPT_FOOTNOTES
    return options


def _parse_with_extensions(
    encoded: bytes, opts: int, extensions: Sequence[str]
):
    """Parse markdown using the streaming parser with extensions attached.

    Returns (node, parser) — caller must free both.
    """
    parser = lib.cmark_parser_new(opts)
    if parser == ffi.NULL:
        raise MemoryError("Failed to create parser")

    for ext_name in extensions:
        lib.cmark_parser_attach_syntax_extension(parser, _get_extension(ext_name))

    lib.cmark_parser_feed(parser, encoded, len(encoded))
    node = lib.cmark_parser_finish(parser)
    if node == ffi.NULL:
        lib.cmark_parser_free(parser)
        raise MemoryError("Failed to parse document")
    return node, parser


def markdown_to_html(
    text: str,
    *,
    hardbreaks: bool = False,
    smart: bool = False,
    normalize: bool = False,
    sourcepos: bool = False,
    unsafe: bool = False,
    footnotes: bool = False,
    extensions: Sequence[str] = (),
    options: int = 0,
) -> str:
    """Parse CommonMark/GFM and render as HTML.

    Takes a Markdown string and returns the corresponding HTML output. By default,
    raw HTML embedded in the Markdown is stripped for security (replaced with an HTML
    comment). Set `unsafe=True` to allow raw HTML passthrough.

    The parser is fully [CommonMark spec](https://spec.commonmark.org/) compliant. When
    GFM extensions are enabled via `extensions=`, additional syntax is recognized
    (tables, strikethrough, autolinks, tag filtering, and task lists).

    Parameters
    ----------
    text : str
        The Markdown string to parse and render. Can be any length, from a single
        inline fragment to a full document. Must be a Python `str` (not bytes).

    hardbreaks : bool
        Render soft line breaks (single newlines within a paragraph) as `<br />` tags.
        By default, this is `False` and soft breaks are rendered as spaces, matching the
        CommonMark specification behavior.

    smart : bool
        Convert straight quotes to curly quotes, `--` to en-dashes, `---` to em-dashes,
        and `...` to ellipses. By default, this is `False`.

    normalize : bool
        Consolidate adjacent text nodes in the parsed AST before rendering. This can
        produce slightly cleaner output in edge cases. By default, this is `False`.

    sourcepos : bool
        Include `data-sourcepos` attributes on block-level HTML elements indicating
        their line/column positions in the original Markdown source. Useful for building
        editors or source-mapping tools. By default, this is `False`.

    unsafe : bool
        Allow raw HTML and potentially dangerous links to pass through to the output
        without sanitization. When `False` (the default), raw HTML blocks and inline
        HTML are replaced with a comment `<!-- raw HTML omitted -->`, and dangerous
        URLs (e.g., `javascript:`) are suppressed.

    footnotes : bool
        Enable footnote syntax parsing. When `True`, `[^label]` markers and
        `[^label]: content` definitions are recognized and rendered as numbered
        footnotes with backlinks. By default, this is `False`.

    extensions : Sequence[str]
        A sequence of GFM extension names to enable during parsing. Valid names are
        `"table"`, `"strikethrough"`, `"autolink"`, `"tagfilter"`, and `"tasklist"`.
        An empty sequence (the default) parses standard CommonMark only.

    options : int
        An integer bitmask of `Options` flags. Build it by OR-ing flags together, e.g.,
        `Options.SMART | Options.UNSAFE`. This value is combined (via OR) with any named
        boolean parameters that are set to `True`, so you can mix both styles freely.
        Defaults to `0` (no additional flags beyond those set by keyword arguments).

    Keyword Arguments vs. Options Flags
    ------------------------------------
    The boolean keyword arguments (`smart`, `unsafe`, `hardbreaks`, etc.) are convenience
    shortcuts for the most common `Options` flags. Using `smart=True` is equivalent to
    passing `options=Options.SMART`. When both are provided, they are merged:
    `markdown_to_html(text, smart=True, options=Options.UNSAFE)` is the same as
    `options=Options.SMART | Options.UNSAFE`.

    Some flags (like `Options.GITHUB_PRE_LANG`, `Options.STRIKETHROUGH_DOUBLE_TILDE`,
    and `Options.LIBERAL_HTML_TAG`) have no keyword shortcut and can only be set via
    the `options` parameter.

    Returns
    -------
    str
        The rendered HTML string. Block-level elements end with a trailing newline.

    Examples
    --------
    Render basic Markdown to HTML:

    ```{python}
    from multimark import markdown_to_html

    markdown_to_html("**bold** and *italic*")
    ```

    Enable smart punctuation:

    ```{python}
    markdown_to_html('"Hello" -- world...', smart=True)
    ```

    Allow raw HTML passthrough:

    ```{python}
    markdown_to_html("<div>custom</div>", unsafe=True)
    ```

    Use GFM table extension:

    ```{python}
    markdown_to_html(
        "| A | B |\\n|---|---|\\n| 1 | 2 |\\n",
        extensions=["table"],
    )
    ```

    Combine multiple features:

    ```{python}
    markdown_to_html(
        "~~old~~ -> new\\n\\nVisit https://example.com\\n",
        extensions=["strikethrough", "autolink"],
        smart=True,
    )
    ```
    """
    opts = _build_options(options, hardbreaks, smart, normalize, sourcepos, unsafe, footnotes)
    encoded = text.encode("utf-8")

    if extensions:
        node, parser = _parse_with_extensions(encoded, opts, extensions)
        ext_list = lib.cmark_parser_get_syntax_extensions(parser)
        try:
            result_ptr = lib.cmark_render_html(node, opts, ext_list)
            if result_ptr == ffi.NULL:
                raise MemoryError("Failed to render document")
            result = ffi.string(result_ptr).decode("utf-8")
            lib.free(result_ptr)
            return result
        finally:
            lib.cmark_node_free(node)
            lib.cmark_parser_free(parser)
    else:
        node = lib.cmark_parse_document(encoded, len(encoded), opts)
        if node == ffi.NULL:
            raise MemoryError("Failed to parse document")
        try:
            result_ptr = lib.cmark_render_html(node, opts, ffi.NULL)
            if result_ptr == ffi.NULL:
                raise MemoryError("Failed to render document")
            result = ffi.string(result_ptr).decode("utf-8")
            lib.free(result_ptr)
            return result
        finally:
            lib.cmark_node_free(node)


def markdown_to_xml(
    text: str,
    *,
    hardbreaks: bool = False,
    smart: bool = False,
    normalize: bool = False,
    sourcepos: bool = False,
    unsafe: bool = False,
    footnotes: bool = False,
    extensions: Sequence[str] = (),
    options: int = 0,
) -> str:
    """Parse CommonMark/GFM and render as XML.

    Produces an XML representation of the parsed abstract syntax tree (AST). Each
    Markdown construct is represented as a named element (e.g., `<paragraph>`,
    `<strong>`, `<code_block>`), with text content preserved in `<text>` elements.

    The XML output conforms to the CommonMark DTD and includes an XML declaration and
    DOCTYPE. This format is useful for debugging, AST inspection, or piping into
    XML-based toolchains.

    Parameters
    ----------
    text : str
        The Markdown string to parse and render. Must be a Python `str`.

    hardbreaks : bool
        Render soft line breaks as hard breaks in the AST. By default, this is `False`.

    smart : bool
        Convert straight quotes to curly quotes, `--` to en-dashes, `---` to em-dashes,
        and `...` to ellipses. By default, this is `False`.

    normalize : bool
        Consolidate adjacent text nodes in the parsed AST. By default, this is `False`.

    sourcepos : bool
        Include `sourcepos` attributes on elements indicating their line/column
        positions in the original Markdown source. By default, this is `False`.

    unsafe : bool
        Allow raw HTML to pass through. By default, this is `False`.

    footnotes : bool
        Enable footnote syntax parsing. By default, this is `False`.

    extensions : Sequence[str]
        A sequence of GFM extension names to enable. Valid names are `"table"`,
        `"strikethrough"`, `"autolink"`, `"tagfilter"`, and `"tasklist"`.

    options : int
        An integer bitmask of `Options` flags (e.g., `Options.SMART | Options.UNSAFE`).
        Merged via OR with any boolean keyword arguments set to `True`.
        Defaults to `0`.

    Keyword Arguments vs. Options Flags
    ------------------------------------
    The boolean keyword arguments (`smart`, `unsafe`, `hardbreaks`, etc.) are convenience
    shortcuts for the most common `Options` flags. When both styles are provided, they
    are merged via OR. See `markdown_to_html()` for a detailed explanation.

    Returns
    -------
    str
        The rendered XML string, including the XML declaration and DOCTYPE.

    Examples
    --------
    Inspect the AST structure of a simple document:

    ```{python}
    from multimark import markdown_to_xml

    print(markdown_to_xml("**hello**"))
    ```

    Add source position information:

    ```{python}
    markdown_to_xml("# Title\\n\\nBody text\\n", sourcepos=True)
    ```
    """
    opts = _build_options(options, hardbreaks, smart, normalize, sourcepos, unsafe, footnotes)
    encoded = text.encode("utf-8")

    if extensions:
        node, parser = _parse_with_extensions(encoded, opts, extensions)
        try:
            result_ptr = lib.cmark_render_xml(node, opts)
            if result_ptr == ffi.NULL:
                raise MemoryError("Failed to render document")
            result = ffi.string(result_ptr).decode("utf-8")
            lib.free(result_ptr)
            return result
        finally:
            lib.cmark_node_free(node)
            lib.cmark_parser_free(parser)
    else:
        node = lib.cmark_parse_document(encoded, len(encoded), opts)
        if node == ffi.NULL:
            raise MemoryError("Failed to parse document")
        try:
            result_ptr = lib.cmark_render_xml(node, opts)
            if result_ptr == ffi.NULL:
                raise MemoryError("Failed to render document")
            result = ffi.string(result_ptr).decode("utf-8")
            lib.free(result_ptr)
            return result
        finally:
            lib.cmark_node_free(node)


def markdown_to_latex(
    text: str,
    *,
    hardbreaks: bool = False,
    smart: bool = False,
    normalize: bool = False,
    unsafe: bool = False,
    footnotes: bool = False,
    extensions: Sequence[str] = (),
    width: int = 0,
    options: int = 0,
) -> str:
    """Parse CommonMark/GFM and render as LaTeX.

    Converts Markdown to LaTeX source suitable for inclusion in a `.tex` document.
    Inline formatting maps to LaTeX commands (`\\textbf{}`, `\\emph{}`, `\\texttt{}`),
    headings become sectioning commands (`\\section{}`, `\\subsection{}`, etc.), and
    links use `\\href{}{}`.

    The output is a fragment (not a full document): it does not include
    `\\documentclass`, `\\begin{document}`, or preamble. You can concatenate it into
    your own LaTeX document structure.

    Parameters
    ----------
    text : str
        The Markdown string to parse and render. Must be a Python `str`.

    hardbreaks : bool
        Render soft line breaks as hard breaks (`\\\\`). By default, this is `False`.

    smart : bool
        Convert straight quotes to curly quotes, `--` to en-dashes, `---` to em-dashes,
        and `...` to ellipses. By default, this is `False`.

    normalize : bool
        Consolidate adjacent text nodes in the parsed AST. By default, this is `False`.

    unsafe : bool
        Allow raw HTML to pass through. Since LaTeX is the target format, raw HTML is
        typically irrelevant. By default, this is `False`.

    footnotes : bool
        Enable footnote syntax parsing. By default, this is `False`.

    extensions : Sequence[str]
        A sequence of GFM extension names to enable. Valid names are `"table"`,
        `"strikethrough"`, `"autolink"`, `"tagfilter"`, and `"tasklist"`.

    width : int
        The column at which to wrap output lines. Set to `0` (the default) to disable
        line wrapping entirely. A value like `80` produces lines of at most 80
        characters where possible.

    options : int
        An integer bitmask of `Options` flags (e.g., `Options.SMART | Options.UNSAFE`).
        Merged via OR with any boolean keyword arguments set to `True`.
        Defaults to `0`.

    Keyword Arguments vs. Options Flags
    ------------------------------------
    The boolean keyword arguments (`smart`, `unsafe`, `hardbreaks`, etc.) are convenience
    shortcuts for the most common `Options` flags. When both styles are provided, they
    are merged via OR. See `markdown_to_html()` for a detailed explanation.

    Returns
    -------
    str
        The rendered LaTeX string.

    Examples
    --------
    Render inline formatting:

    ```{python}
    from multimark import markdown_to_latex

    markdown_to_latex("**bold** and *italic*")
    ```

    Render a heading:

    ```{python}
    markdown_to_latex("# Introduction")
    ```

    Enable line wrapping at 72 columns:

    ```{python}
    long_text = "This is a very long paragraph. " * 10
    print(markdown_to_latex(long_text, width=72))
    ```

    Use smart punctuation for typographic output:

    ```{python}
    markdown_to_latex('"Hello," she said --- "goodbye."', smart=True)
    ```
    """
    opts = _build_options(options, hardbreaks, smart, normalize, False, unsafe, footnotes)
    encoded = text.encode("utf-8")

    if extensions:
        node, parser = _parse_with_extensions(encoded, opts, extensions)
        try:
            result_ptr = lib.cmark_render_latex(node, opts, width)
            if result_ptr == ffi.NULL:
                raise MemoryError("Failed to render document")
            result = ffi.string(result_ptr).decode("utf-8", errors="replace")
            lib.free(result_ptr)
            return result
        finally:
            lib.cmark_node_free(node)
            lib.cmark_parser_free(parser)
    else:
        node = lib.cmark_parse_document(encoded, len(encoded), opts)
        if node == ffi.NULL:
            raise MemoryError("Failed to parse document")
        try:
            result_ptr = lib.cmark_render_latex(node, opts, width)
            if result_ptr == ffi.NULL:
                raise MemoryError("Failed to render document")
            result = ffi.string(result_ptr).decode("utf-8", errors="replace")
            lib.free(result_ptr)
            return result
        finally:
            lib.cmark_node_free(node)


def markdown_to_man(
    text: str,
    *,
    hardbreaks: bool = False,
    smart: bool = False,
    normalize: bool = False,
    unsafe: bool = False,
    footnotes: bool = False,
    extensions: Sequence[str] = (),
    width: int = 0,
    options: int = 0,
) -> str:
    """Parse CommonMark/GFM and render as a groff man page.

    Produces groff-format output suitable for use with the `man` command or inclusion
    in manual page source files. Inline formatting maps to font switching requests
    (`\\f[B]`, `\\f[I]`, `\\f[CR]`), paragraphs use `.PP`, and headings use `.SH` or
    `.SS` macros.

    The output is a fragment and does not include a `.TH` title header. Wrap it in your
    own man page structure to produce a complete manual page.

    Parameters
    ----------
    text : str
        The Markdown string to parse and render. Must be a Python `str`.

    hardbreaks : bool
        Render soft line breaks as hard breaks (`.br`). By default, this is `False`.

    smart : bool
        Convert straight quotes to curly quotes, `--` to en-dashes, `---` to em-dashes,
        and `...` to ellipses. By default, this is `False`.

    normalize : bool
        Consolidate adjacent text nodes in the parsed AST. By default, this is `False`.

    unsafe : bool
        Allow raw HTML to pass through. Since groff is the target format, raw HTML is
        typically irrelevant. By default, this is `False`.

    footnotes : bool
        Enable footnote syntax parsing. By default, this is `False`.

    extensions : Sequence[str]
        A sequence of GFM extension names to enable. Valid names are `"table"`,
        `"strikethrough"`, `"autolink"`, `"tagfilter"`, and `"tasklist"`.

    width : int
        The column at which to wrap output lines. Set to `0` (the default) to disable
        line wrapping entirely.

    options : int
        An integer bitmask of `Options` flags (e.g., `Options.SMART | Options.UNSAFE`).
        Merged via OR with any boolean keyword arguments set to `True`.
        Defaults to `0`.

    Keyword Arguments vs. Options Flags
    ------------------------------------
    The boolean keyword arguments (`smart`, `unsafe`, `hardbreaks`, etc.) are convenience
    shortcuts for the most common `Options` flags. When both styles are provided, they
    are merged via OR. See `markdown_to_html()` for a detailed explanation.

    Returns
    -------
    str
        The rendered groff man page string.

    Examples
    --------
    Render a paragraph with bold and italic:

    ```{python}
    from multimark import markdown_to_man

    markdown_to_man("**bold** and *italic*")
    ```

    Render a heading:

    ```{python}
    markdown_to_man("## Options")
    ```

    Wrap at 72 columns:

    ```{python}
    long_paragraph = "This is a long paragraph of text. " * 10
    print(markdown_to_man(long_paragraph, width=72))
    ```
    """
    opts = _build_options(options, hardbreaks, smart, normalize, False, unsafe, footnotes)
    encoded = text.encode("utf-8")

    if extensions:
        node, parser = _parse_with_extensions(encoded, opts, extensions)
        try:
            result_ptr = lib.cmark_render_man(node, opts, width)
            if result_ptr == ffi.NULL:
                raise MemoryError("Failed to render document")
            result = ffi.string(result_ptr).decode("utf-8", errors="replace")
            lib.free(result_ptr)
            return result
        finally:
            lib.cmark_node_free(node)
            lib.cmark_parser_free(parser)
    else:
        node = lib.cmark_parse_document(encoded, len(encoded), opts)
        if node == ffi.NULL:
            raise MemoryError("Failed to parse document")
        try:
            result_ptr = lib.cmark_render_man(node, opts, width)
            if result_ptr == ffi.NULL:
                raise MemoryError("Failed to render document")
            result = ffi.string(result_ptr).decode("utf-8", errors="replace")
            lib.free(result_ptr)
            return result
        finally:
            lib.cmark_node_free(node)


def markdown_to_commonmark(
    text: str,
    *,
    hardbreaks: bool = False,
    smart: bool = False,
    normalize: bool = False,
    unsafe: bool = False,
    footnotes: bool = False,
    extensions: Sequence[str] = (),
    width: int = 0,
    options: int = 0,
) -> str:
    """Parse CommonMark/GFM and render back as normalized CommonMark.

    Parses the input Markdown into an AST and re-renders it as CommonMark. This
    effectively normalizes the formatting: different but semantically equivalent
    Markdown inputs (e.g., `*italic*` vs `_italic_`, varying list indentation) will
    produce a canonical output form.

    This is useful for round-trip testing, canonical formatting, or cleaning up
    inconsistently formatted documents. The output of this function, when parsed again,
    produces the same AST as the original input.

    Parameters
    ----------
    text : str
        The Markdown string to parse and normalize. Must be a Python `str`.

    hardbreaks : bool
        Render soft line breaks as hard breaks (backslash-newline). By default, this is
        `False`.

    smart : bool
        Convert straight quotes to curly quotes, `--` to en-dashes, `---` to em-dashes,
        and `...` to ellipses. By default, this is `False`.

    normalize : bool
        Consolidate adjacent text nodes in the parsed AST. By default, this is `False`.

    unsafe : bool
        Allow raw HTML to pass through. By default, this is `False`, which replaces raw
        HTML with a comment placeholder.

    footnotes : bool
        Enable footnote syntax parsing. By default, this is `False`.

    extensions : Sequence[str]
        A sequence of GFM extension names to enable. Valid names are `"table"`,
        `"strikethrough"`, `"autolink"`, `"tagfilter"`, and `"tasklist"`.

    width : int
        The column at which to wrap output lines. Set to `0` (the default) to disable
        line wrapping entirely. This is useful for producing line-wrapped output for
        version-control-friendly diffs.

    options : int
        An integer bitmask of `Options` flags (e.g., `Options.SMART | Options.UNSAFE`).
        Merged via OR with any boolean keyword arguments set to `True`.
        Defaults to `0`.

    Keyword Arguments vs. Options Flags
    ------------------------------------
    The boolean keyword arguments (`smart`, `unsafe`, `hardbreaks`, etc.) are convenience
    shortcuts for the most common `Options` flags. When both styles are provided, they
    are merged via OR. See `markdown_to_html()` for a detailed explanation.

    Returns
    -------
    str
        The normalized CommonMark string.

    Examples
    --------
    Normalize inconsistent formatting:

    ```{python}
    from multimark import markdown_to_commonmark

    markdown_to_commonmark("_hello_ **world**")
    ```

    Verify round-trip stability (parse, render, re-parse produces the same HTML):

    ```{python}
    from multimark import markdown_to_commonmark, markdown_to_html

    original = "**bold** and *italic*"
    normalized = markdown_to_commonmark(original)
    assert markdown_to_html(original) == markdown_to_html(normalized)
    ```

    Wrap at 80 columns for version-control-friendly output:

    ```{python}
    long_document = "This is a long sentence for demonstration. " * 10
    print(markdown_to_commonmark(long_document, width=80))
    ```
    """
    opts = _build_options(options, hardbreaks, smart, normalize, False, unsafe, footnotes)
    encoded = text.encode("utf-8")

    if extensions:
        node, parser = _parse_with_extensions(encoded, opts, extensions)
        try:
            result_ptr = lib.cmark_render_commonmark(node, opts, width)
            if result_ptr == ffi.NULL:
                raise MemoryError("Failed to render document")
            result = ffi.string(result_ptr).decode("utf-8", errors="replace")
            lib.free(result_ptr)
            return result
        finally:
            lib.cmark_node_free(node)
            lib.cmark_parser_free(parser)
    else:
        node = lib.cmark_parse_document(encoded, len(encoded), opts)
        if node == ffi.NULL:
            raise MemoryError("Failed to parse document")
        try:
            result_ptr = lib.cmark_render_commonmark(node, opts, width)
            if result_ptr == ffi.NULL:
                raise MemoryError("Failed to render document")
            result = ffi.string(result_ptr).decode("utf-8", errors="replace")
            lib.free(result_ptr)
            return result
        finally:
            lib.cmark_node_free(node)


def cmark_version() -> str:
    """Return the version string of the vendored cmark-gfm library.

    Reports the version of the bundled cmark-gfm C library that multimark was compiled
    against. This is useful for debugging or confirming which release of the underlying
    parser is in use.

    Returns
    -------
    str
        A version string in the format `"X.Y.Z.gfm.N"` (e.g., `"0.29.0.gfm.13"`).

    Examples
    --------
    ```{python}
    from multimark import cmark_version

    cmark_version()
    ```
    """
    return ffi.string(lib.cmark_version_string()).decode("utf-8")
