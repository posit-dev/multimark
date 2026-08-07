from __future__ import annotations

from typing import Sequence

from multimark._binding import ffi, lib
from multimark._cmark import _build_options, _get_extension, VALID_EXTENSIONS


class Parser:
    """Streaming CommonMark/GFM parser.

    Wraps the cmark-gfm streaming parser, allowing incremental feeding of Markdown
    content and rendering to any output format. Useful for processing large documents
    or streaming input without buffering the entire source in memory.

    Parameters
    ----------
    hardbreaks
        Render soft line breaks as hard breaks. Default `False`.
    smart
        Enable smart punctuation. Default `False`.
    normalize
        Consolidate adjacent text nodes. Default `False`.
    unsafe
        Allow raw HTML passthrough. Default `False`.
    footnotes
        Enable footnote syntax. Default `False`.
    extensions
        GFM extensions to enable (e.g., `["table", "strikethrough"]`).
    options
        Raw `Options` bitmask, OR'd with boolean kwargs.

    Examples
    --------
    Basic streaming usage:

    ```python
    from multimark import Parser

    parser = Parser(smart=True)
    parser.feed("# Hello\\n\\n")
    parser.feed("World!\\n")
    html = parser.render_html()
    ```

    Context manager:

    ```python
    with Parser(extensions=["table"]) as p:
        p.feed("| A | B |\\n|---|---|\\n| 1 | 2 |\\n")
        html = p.render_html()
    ```
    """

    def __init__(
        self,
        *,
        hardbreaks: bool = False,
        smart: bool = False,
        normalize: bool = False,
        unsafe: bool = False,
        footnotes: bool = False,
        extensions: Sequence[str] = (),
        options: int = 0,
    ) -> None:
        self._opts = _build_options(
            options, hardbreaks, smart, normalize, False, unsafe, footnotes
        )
        self._extensions = list(extensions)
        self._finished = False
        self._node = ffi.NULL
        self._parser = lib.cmark_parser_new(self._opts)
        if self._parser == ffi.NULL:
            raise MemoryError("Failed to create parser")

        for ext_name in self._extensions:
            if ext_name not in VALID_EXTENSIONS:
                lib.cmark_parser_free(self._parser)
                self._parser = ffi.NULL
                raise ValueError(
                    f"Unknown extension: {ext_name!r}. "
                    f"Valid extensions: {sorted(VALID_EXTENSIONS)}"
                )
            lib.cmark_parser_attach_syntax_extension(
                self._parser, _get_extension(ext_name)
            )

    def feed(self, text: str) -> None:
        """Feed a chunk of Markdown text to the parser.

        May be called multiple times before finishing. The concatenation of all fed
        chunks forms the complete document.

        Parameters
        ----------
        text
            Markdown content to append to the parse buffer.

        Raises
        ------
        ValueError
            If the parser has already been finished or closed.
        TypeError
            If *text* is not a string.
        """
        if self._parser == ffi.NULL:
            raise ValueError("Parser is closed")
        if self._finished:
            raise ValueError("Parser has already been finished; create a new Parser")
        if not isinstance(text, str):
            raise TypeError(f"Expected str, got {type(text).__name__}")
        encoded = text.encode("utf-8")
        lib.cmark_parser_feed(self._parser, encoded, len(encoded))

    def _finish(self) -> None:
        """Finalize parsing and obtain the AST root node."""
        if self._finished:
            return
        if self._parser == ffi.NULL:
            raise ValueError("Parser is closed")
        self._node = lib.cmark_parser_finish(self._parser)
        if self._node == ffi.NULL:
            raise MemoryError("Failed to parse document")
        self._finished = True

    def finish(self):
        """Finalize parsing and return the root Node of the AST.

        After calling this method, no more text can be fed to the parser.
        The returned Node can be used for tree inspection or rendering.

        Returns
        -------
        Node
            The root document node of the parsed AST.

        Raises
        ------
        ValueError
            If the parser is closed.
        """
        from multimark._node import Node

        self._finish()
        return Node._from_ptr(self._node, owner=self)

    def render_html(self, *, sourcepos: bool = False) -> str:
        """Finish parsing (if needed) and render as HTML.

        Parameters
        ----------
        sourcepos
            Include `data-sourcepos` attributes. Default `False`.

        Returns
        -------
        str
            The rendered HTML string.
        """
        self._finish()
        opts = self._opts
        if sourcepos:
            opts |= lib.CMARK_OPT_SOURCEPOS
        ext_list = lib.cmark_parser_get_syntax_extensions(self._parser)
        result_ptr = lib.cmark_render_html(self._node, opts, ext_list)
        if result_ptr == ffi.NULL:
            raise MemoryError("Failed to render document")
        result = ffi.string(result_ptr).decode("utf-8")
        lib.free(result_ptr)
        return result

    def render_xml(self, *, sourcepos: bool = False) -> str:
        """Finish parsing (if needed) and render as XML.

        Parameters
        ----------
        sourcepos
            Include `sourcepos` attributes. Default `False`.

        Returns
        -------
        str
            The rendered XML string.
        """
        self._finish()
        opts = self._opts
        if sourcepos:
            opts |= lib.CMARK_OPT_SOURCEPOS
        result_ptr = lib.cmark_render_xml(self._node, opts)
        if result_ptr == ffi.NULL:
            raise MemoryError("Failed to render document")
        result = ffi.string(result_ptr).decode("utf-8")
        lib.free(result_ptr)
        return result

    def render_latex(self, *, width: int = 0) -> str:
        """Finish parsing (if needed) and render as LaTeX.

        Parameters
        ----------
        width
            Line wrapping column (0 = no wrapping). Default `0`.

        Returns
        -------
        str
            The rendered LaTeX string.
        """
        self._finish()
        result_ptr = lib.cmark_render_latex(self._node, self._opts, width)
        if result_ptr == ffi.NULL:
            raise MemoryError("Failed to render document")
        result = ffi.string(result_ptr).decode("utf-8", errors="replace")
        lib.free(result_ptr)
        return result

    def render_man(self, *, width: int = 0) -> str:
        """Finish parsing (if needed) and render as a groff man page.

        Parameters
        ----------
        width
            Line wrapping column (0 = no wrapping). Default `0`.

        Returns
        -------
        str
            The rendered man page string.
        """
        self._finish()
        result_ptr = lib.cmark_render_man(self._node, self._opts, width)
        if result_ptr == ffi.NULL:
            raise MemoryError("Failed to render document")
        result = ffi.string(result_ptr).decode("utf-8", errors="replace")
        lib.free(result_ptr)
        return result

    def render_commonmark(self, *, width: int = 0) -> str:
        """Finish parsing (if needed) and render as normalized CommonMark.

        Parameters
        ----------
        width
            Line wrapping column (0 = no wrapping). Default `0`.

        Returns
        -------
        str
            The normalized CommonMark string.
        """
        self._finish()
        result_ptr = lib.cmark_render_commonmark(self._node, self._opts, width)
        if result_ptr == ffi.NULL:
            raise MemoryError("Failed to render document")
        result = ffi.string(result_ptr).decode("utf-8", errors="replace")
        lib.free(result_ptr)
        return result

    def close(self) -> None:
        """Release all C resources held by this parser.

        After closing, the parser cannot be used. This is called automatically
        when used as a context manager.
        """
        if self._node != ffi.NULL:
            lib.cmark_node_free(self._node)
            self._node = ffi.NULL
        if self._parser != ffi.NULL:
            lib.cmark_parser_free(self._parser)
            self._parser = ffi.NULL

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def __del__(self):
        self.close()
