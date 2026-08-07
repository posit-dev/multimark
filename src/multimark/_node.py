from __future__ import annotations

import weakref
from enum import IntEnum
from typing import Generator, Sequence

from multimark._binding import ffi, lib
from multimark._cmark import _build_options, _get_extension, VALID_EXTENSIONS


class NodeType(IntEnum):
    """CommonMark/GFM AST node types."""

    NONE = lib.CMARK_NODE_NONE
    # Block nodes
    DOCUMENT = lib.CMARK_NODE_DOCUMENT
    BLOCK_QUOTE = lib.CMARK_NODE_BLOCK_QUOTE
    LIST = lib.CMARK_NODE_LIST
    ITEM = lib.CMARK_NODE_ITEM
    CODE_BLOCK = lib.CMARK_NODE_CODE_BLOCK
    HTML_BLOCK = lib.CMARK_NODE_HTML_BLOCK
    CUSTOM_BLOCK = lib.CMARK_NODE_CUSTOM_BLOCK
    PARAGRAPH = lib.CMARK_NODE_PARAGRAPH
    HEADING = lib.CMARK_NODE_HEADING
    THEMATIC_BREAK = lib.CMARK_NODE_THEMATIC_BREAK
    FOOTNOTE_DEFINITION = lib.CMARK_NODE_FOOTNOTE_DEFINITION
    # Inline nodes
    TEXT = lib.CMARK_NODE_TEXT
    SOFTBREAK = lib.CMARK_NODE_SOFTBREAK
    LINEBREAK = lib.CMARK_NODE_LINEBREAK
    CODE = lib.CMARK_NODE_CODE
    HTML_INLINE = lib.CMARK_NODE_HTML_INLINE
    CUSTOM_INLINE = lib.CMARK_NODE_CUSTOM_INLINE
    EMPH = lib.CMARK_NODE_EMPH
    STRONG = lib.CMARK_NODE_STRONG
    LINK = lib.CMARK_NODE_LINK
    IMAGE = lib.CMARK_NODE_IMAGE
    FOOTNOTE_REFERENCE = lib.CMARK_NODE_FOOTNOTE_REFERENCE


class ListType(IntEnum):
    """List type for LIST nodes."""

    NONE = lib.CMARK_NO_LIST
    BULLET = lib.CMARK_BULLET_LIST
    ORDERED = lib.CMARK_ORDERED_LIST


class DelimType(IntEnum):
    """Delimiter type for ordered lists."""

    NONE = lib.CMARK_NO_DELIM
    PERIOD = lib.CMARK_PERIOD_DELIM
    PAREN = lib.CMARK_PAREN_DELIM


class Node:
    """A node in the CommonMark/GFM abstract syntax tree.

    Nodes are obtained by calling `parse()` or `Parser.finish()`. They should not be
    instantiated directly.

    Provides tree traversal, node property access, and rendering methods.
    """

    # Identity map: pointer address → weak reference to Node wrapper.
    # Ensures `node.next is node.next` holds True for the same tree.
    _identity_map: dict[int, weakref.ref[Node]] = {}

    __slots__ = ("_ptr", "_owner", "__weakref__")

    def __init__(self, ptr, owner):
        self._ptr = ptr
        # owner keeps the root node (and thus the whole C tree) alive.
        # For root nodes, owner is the Parser or a ref-holding sentinel.
        self._owner = owner

    @classmethod
    def _from_ptr(cls, ptr, owner) -> Node | None:
        """Get or create a Node wrapper for a C pointer."""
        if ptr == ffi.NULL:
            return None
        addr = int(ffi.cast("uintptr_t", ptr))
        ref = cls._identity_map.get(addr)
        if ref is not None:
            node = ref()
            if node is not None:
                return node
        node = cls.__new__(cls)
        node._ptr = ptr
        node._owner = owner
        cls._identity_map[addr] = weakref.ref(node, lambda r, a=addr: cls._identity_map.pop(a, None))
        return node

    @classmethod
    def new(cls, node_type: NodeType) -> Node:
        """Create a new detached node of the given type.

        The node is not part of any tree. Use mutation methods
        (`append_child()`, `insert_before()`, etc.) to attach it.

        Parameters
        ----------
        node_type : NodeType
            The type of node to create.

        Returns
        -------
        Node
            A new detached node.
        """
        ptr = lib.cmark_node_new(int(node_type))
        if ptr == ffi.NULL:
            raise MemoryError("Failed to create node")
        node = cls.__new__(cls)
        node._ptr = ptr

        # Detached nodes own themselves; stored as a prevent-GC ref.
        node._owner = node
        addr = int(ffi.cast("uintptr_t", ptr))
        cls._identity_map[addr] = weakref.ref(node, lambda r, a=addr: cls._identity_map.pop(a, None))
        return node

    def _check_alive(self):
        if self._ptr == ffi.NULL:
            raise ValueError("Node has been freed")

    # -- Tree traversal --

    @property
    def type(self) -> NodeType:
        """The node type."""
        self._check_alive()
        raw = lib.cmark_node_get_type(self._ptr)
        try:
            return NodeType(raw)
        except ValueError:
            # Extension node types may not be in our enum
            return raw

    @property
    def type_string(self) -> str:
        """Human-readable node type name from cmark (e.g., `'heading'`)."""
        self._check_alive()
        ptr = lib.cmark_node_get_type_string(self._ptr)
        if ptr == ffi.NULL:
            return "none"
        return ffi.string(ptr).decode("utf-8")

    @property
    def parent(self) -> Node | None:
        """The parent node, or `None` if this is the root."""
        self._check_alive()
        return Node._from_ptr(lib.cmark_node_parent(self._ptr), self._owner)

    @property
    def first_child(self) -> Node | None:
        """The first child node, or `None`."""
        self._check_alive()
        return Node._from_ptr(lib.cmark_node_first_child(self._ptr), self._owner)

    @property
    def last_child(self) -> Node | None:
        """The last child node, or `None`."""
        self._check_alive()
        return Node._from_ptr(lib.cmark_node_last_child(self._ptr), self._owner)

    @property
    def next(self) -> Node | None:
        """The next sibling, or `None`."""
        self._check_alive()
        return Node._from_ptr(lib.cmark_node_next(self._ptr), self._owner)

    @property
    def previous(self) -> Node | None:
        """The previous sibling, or `None`."""
        self._check_alive()
        return Node._from_ptr(lib.cmark_node_previous(self._ptr), self._owner)

    @property
    def children(self) -> Generator[Node, None, None]:
        """Iterate over direct child nodes."""
        self._check_alive()
        child = lib.cmark_node_first_child(self._ptr)
        while child != ffi.NULL:
            yield Node._from_ptr(child, self._owner)
            child = lib.cmark_node_next(child)

    # -- Node properties --

    @property
    def literal(self) -> str | None:
        """Text content for text, code, and HTML nodes. `None` if not applicable."""
        self._check_alive()
        ptr = lib.cmark_node_get_literal(self._ptr)
        if ptr == ffi.NULL:
            return None
        return ffi.string(ptr).decode("utf-8")

    @literal.setter
    def literal(self, value: str) -> None:
        self._check_alive()
        if not isinstance(value, str):
            raise TypeError(f"Expected str, got {type(value).__name__}")
        rc = lib.cmark_node_set_literal(self._ptr, value.encode("utf-8"))
        if rc == 0:
            raise ValueError("Cannot set literal on this node type")

    @property
    def url(self) -> str | None:
        """URL for link and image nodes. `None` if not applicable."""
        self._check_alive()
        ptr = lib.cmark_node_get_url(self._ptr)
        if ptr == ffi.NULL:
            return None
        return ffi.string(ptr).decode("utf-8")

    @url.setter
    def url(self, value: str) -> None:
        self._check_alive()
        if not isinstance(value, str):
            raise TypeError(f"Expected str, got {type(value).__name__}")
        rc = lib.cmark_node_set_url(self._ptr, value.encode("utf-8"))
        if rc == 0:
            raise ValueError("Cannot set URL on this node type")

    @property
    def title(self) -> str | None:
        """Title for link and image nodes. `None` if not applicable."""
        self._check_alive()
        ptr = lib.cmark_node_get_title(self._ptr)
        if ptr == ffi.NULL:
            return None
        return ffi.string(ptr).decode("utf-8")

    @title.setter
    def title(self, value: str) -> None:
        self._check_alive()
        if not isinstance(value, str):
            raise TypeError(f"Expected str, got {type(value).__name__}")
        rc = lib.cmark_node_set_title(self._ptr, value.encode("utf-8"))
        if rc == 0:
            raise ValueError("Cannot set title on this node type")

    @property
    def heading_level(self) -> int:
        """Heading level (1–6) for `HEADING` nodes; 0 otherwise."""
        self._check_alive()
        return lib.cmark_node_get_heading_level(self._ptr)

    @heading_level.setter
    def heading_level(self, value: int) -> None:
        self._check_alive()
        rc = lib.cmark_node_set_heading_level(self._ptr, value)
        if rc == 0:
            raise ValueError("Cannot set heading level on this node type")

    @property
    def list_type(self) -> ListType:
        """List type (`BULLET` or `ORDERED`) for `LIST` nodes."""
        self._check_alive()
        return ListType(lib.cmark_node_get_list_type(self._ptr))

    @list_type.setter
    def list_type(self, value: ListType) -> None:
        self._check_alive()
        rc = lib.cmark_node_set_list_type(self._ptr, int(value))
        if rc == 0:
            raise ValueError("Cannot set list type on this node type")

    @property
    def list_delim(self) -> DelimType:
        """Delimiter type for ordered `LIST` nodes."""
        self._check_alive()
        return DelimType(lib.cmark_node_get_list_delim(self._ptr))

    @property
    def list_start(self) -> int:
        """Starting number for ordered `LIST` nodes; 0 otherwise."""
        self._check_alive()
        return lib.cmark_node_get_list_start(self._ptr)

    @list_start.setter
    def list_start(self, value: int) -> None:
        self._check_alive()
        rc = lib.cmark_node_set_list_start(self._ptr, value)
        if rc == 0:
            raise ValueError("Cannot set list start on this node type")

    @property
    def list_tight(self) -> bool:
        """Whether a `LIST` node is tight (no blank lines between items)."""
        self._check_alive()
        return bool(lib.cmark_node_get_list_tight(self._ptr))

    @list_tight.setter
    def list_tight(self, value: bool) -> None:
        self._check_alive()
        rc = lib.cmark_node_set_list_tight(self._ptr, int(value))
        if rc == 0:
            raise ValueError("Cannot set list tight on this node type")

    @property
    def fence_info(self) -> str | None:
        """Info string for fenced `CODE_BLOCK` nodes (e.g., `'python'`)."""
        self._check_alive()
        ptr = lib.cmark_node_get_fence_info(self._ptr)
        if ptr == ffi.NULL:
            return None
        return ffi.string(ptr).decode("utf-8")

    @fence_info.setter
    def fence_info(self, value: str) -> None:
        self._check_alive()
        if not isinstance(value, str):
            raise TypeError(f"Expected str, got {type(value).__name__}")
        rc = lib.cmark_node_set_fence_info(self._ptr, value.encode("utf-8"))
        if rc == 0:
            raise ValueError("Cannot set fence info on this node type")

    # -- Source positions --

    @property
    def start_line(self) -> int:
        """Start line (1-based) in source. 0 if not available."""
        self._check_alive()
        return lib.cmark_node_get_start_line(self._ptr)

    @property
    def start_column(self) -> int:
        """Start column (1-based) in source. 0 if not available."""
        self._check_alive()
        return lib.cmark_node_get_start_column(self._ptr)

    @property
    def end_line(self) -> int:
        """End line (1-based) in source. 0 if not available."""
        self._check_alive()
        return lib.cmark_node_get_end_line(self._ptr)

    @property
    def end_column(self) -> int:
        """End column (1-based) in source. 0 if not available."""
        self._check_alive()
        return lib.cmark_node_get_end_column(self._ptr)

    # -- Iterator / walk --

    def walk(self) -> Generator[tuple[str, Node], None, None]:
        """Depth-first walk of the subtree rooted at this node.

        Yields `(event, node)` pairs where *event* is `"enter"` or `"exit"`.
        Leaf nodes (`text`, `softbreak`, `linebreak`, `code`, `thematic_break`, `html`) only
        produce an `"enter"` event.

        Examples
        --------
        ```python
        for event, node in doc.walk():
            if event == "enter" and node.type == NodeType.HEADING:
                print(f"Heading level {node.heading_level}")
        ```
        """
        self._check_alive()
        it = lib.cmark_iter_new(self._ptr)
        if it == ffi.NULL:
            raise MemoryError("Failed to create iterator")
        try:
            while True:
                ev = lib.cmark_iter_next(it)
                if ev == lib.CMARK_EVENT_DONE:
                    break
                cur = lib.cmark_iter_get_node(it)
                event_str = "enter" if ev == lib.CMARK_EVENT_ENTER else "exit"
                yield event_str, Node._from_ptr(cur, self._owner)
        finally:
            lib.cmark_iter_free(it)

    # -- Mutation --

    def unlink(self) -> None:
        """Remove this node from its parent tree."""
        self._check_alive()
        lib.cmark_node_unlink(self._ptr)
        # After unlinking, this node owns itself
        self._owner = self

    def insert_before(self, sibling: Node) -> None:
        """Insert *sibling* as the node immediately before this one."""
        self._check_alive()
        sibling._check_alive()
        rc = lib.cmark_node_insert_before(self._ptr, sibling._ptr)
        if rc == 0:
            raise ValueError("Failed to insert node before")
        sibling._owner = self._owner

    def insert_after(self, sibling: Node) -> None:
        """Insert *sibling* as the node immediately after this one."""
        self._check_alive()
        sibling._check_alive()
        rc = lib.cmark_node_insert_after(self._ptr, sibling._ptr)
        if rc == 0:
            raise ValueError("Failed to insert node after")
        sibling._owner = self._owner

    def append_child(self, child: Node) -> None:
        """Append *child* as the last child of this node."""
        self._check_alive()
        child._check_alive()
        rc = lib.cmark_node_append_child(self._ptr, child._ptr)
        if rc == 0:
            raise ValueError("Failed to append child")
        child._owner = self._owner

    def prepend_child(self, child: Node) -> None:
        """Prepend *child* as the first child of this node."""
        self._check_alive()
        child._check_alive()
        rc = lib.cmark_node_prepend_child(self._ptr, child._ptr)
        if rc == 0:
            raise ValueError("Failed to prepend child")
        child._owner = self._owner

    def replace(self, new_node: Node) -> None:
        """Replace this node in the tree with *new_node*."""
        self._check_alive()
        new_node._check_alive()
        rc = lib.cmark_node_replace(self._ptr, new_node._ptr)
        if rc == 0:
            raise ValueError("Failed to replace node")
        new_node._owner = self._owner
        self._owner = self  # detached now

    # -- Rendering --

    def render_html(self, *, sourcepos: bool = False, unsafe: bool = False) -> str:
        """Render this subtree as HTML."""
        self._check_alive()
        opts = 0
        if sourcepos:
            opts |= lib.CMARK_OPT_SOURCEPOS
        if unsafe:
            opts |= lib.CMARK_OPT_UNSAFE
        result_ptr = lib.cmark_render_html(self._ptr, opts, ffi.NULL)
        if result_ptr == ffi.NULL:
            raise MemoryError("Failed to render")
        result = ffi.string(result_ptr).decode("utf-8")
        lib.free(result_ptr)
        return result

    def render_xml(self, *, sourcepos: bool = False) -> str:
        """Render this subtree as XML."""
        self._check_alive()
        opts = 0
        if sourcepos:
            opts |= lib.CMARK_OPT_SOURCEPOS
        result_ptr = lib.cmark_render_xml(self._ptr, opts)
        if result_ptr == ffi.NULL:
            raise MemoryError("Failed to render")
        result = ffi.string(result_ptr).decode("utf-8")
        lib.free(result_ptr)
        return result

    def render_latex(self, *, width: int = 0) -> str:
        """Render this subtree as LaTeX."""
        self._check_alive()
        result_ptr = lib.cmark_render_latex(self._ptr, 0, width)
        if result_ptr == ffi.NULL:
            raise MemoryError("Failed to render")
        result = ffi.string(result_ptr).decode("utf-8", errors="replace")
        lib.free(result_ptr)
        return result

    def render_man(self, *, width: int = 0) -> str:
        """Render this subtree as a groff man page."""
        self._check_alive()
        result_ptr = lib.cmark_render_man(self._ptr, 0, width)
        if result_ptr == ffi.NULL:
            raise MemoryError("Failed to render")
        result = ffi.string(result_ptr).decode("utf-8", errors="replace")
        lib.free(result_ptr)
        return result

    def render_commonmark(self, *, width: int = 0) -> str:
        """Render this subtree as normalized CommonMark."""
        self._check_alive()
        result_ptr = lib.cmark_render_commonmark(self._ptr, 0, width)
        if result_ptr == ffi.NULL:
            raise MemoryError("Failed to render")
        result = ffi.string(result_ptr).decode("utf-8", errors="replace")
        lib.free(result_ptr)
        return result

    # -- Dunder methods --

    def __repr__(self) -> str:
        if self._ptr == ffi.NULL:
            return "<Node (freed)>"
        type_str = self.type_string
        extra = ""
        if self.type == NodeType.HEADING:
            extra = f" level={self.heading_level}"
        elif self.type in (NodeType.TEXT, NodeType.CODE):
            lit = self.literal
            if lit and len(lit) > 30:
                lit = lit[:27] + "..."
            extra = f" {lit!r}"
        elif self.type in (NodeType.LINK, NodeType.IMAGE):
            extra = f" url={self.url!r}"
        return f"<Node {type_str}{extra}>"

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self._ptr == other._ptr

    def __hash__(self):
        return hash(int(ffi.cast("uintptr_t", self._ptr)))


def parse(
    text: str,
    *,
    hardbreaks: bool = False,
    smart: bool = False,
    normalize: bool = False,
    unsafe: bool = False,
    footnotes: bool = False,
    extensions: Sequence[str] = (),
    options: int = 0,
) -> Node:
    """Parse a Markdown string and return the root AST node.

    This is the primary entry point for AST-based document inspection and transformation. The
    returned `Node` provides tree traversal, property access, mutation, and rendering methods.

    Parameters
    ----------
    text
        The Markdown string to parse.
    hardbreaks
        Render soft breaks as hard breaks. Default `False`.
    smart
        Enable smart punctuation. Default `False`.
    normalize
        Consolidate adjacent text nodes. Default `False`.
    unsafe
        Allow raw HTML passthrough. Default `False`.
    footnotes
        Enable footnote syntax. Default `False`.
    extensions
        GFM extensions to enable.
    options
        Raw `Options` bitmask.

    Returns
    -------
    Node
        The root document node. Its `~Node.type()` is `NodeType.DOCUMENT`.

    Examples
    --------
    ```python
    from multimark import parse, NodeType

    doc = parse("# Hello\\n\\nWorld!\\n")
    for event, node in doc.walk():
        if event == "enter" and node.type == NodeType.HEADING:
            print(f"Found heading level {node.heading_level}")
    ```
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    opts = _build_options(options, hardbreaks, smart, normalize, False, unsafe, footnotes)
    encoded = text.encode("utf-8")

    if extensions:
        # Validate extension names
        for ext_name in extensions:
            if ext_name not in VALID_EXTENSIONS:
                raise ValueError(
                    f"Unknown extension: {ext_name!r}. "
                    f"Valid extensions: {sorted(VALID_EXTENSIONS)}"
                )

        parser_ptr = lib.cmark_parser_new(opts)
        if parser_ptr == ffi.NULL:
            raise MemoryError("Failed to create parser")
        for ext_name in extensions:
            lib.cmark_parser_attach_syntax_extension(parser_ptr, _get_extension(ext_name))
        lib.cmark_parser_feed(parser_ptr, encoded, len(encoded))
        node_ptr = lib.cmark_parser_finish(parser_ptr)
        if node_ptr == ffi.NULL:
            lib.cmark_parser_free(parser_ptr)
            raise MemoryError("Failed to parse document")
        # Create an owner object that will free both node and parser on GC
        owner = _ParseResult(node_ptr, parser_ptr)
    else:
        node_ptr = lib.cmark_parse_document(encoded, len(encoded), opts)
        if node_ptr == ffi.NULL:
            raise MemoryError("Failed to parse document")
        owner = _ParseResult(node_ptr, ffi.NULL)

    return Node._from_ptr(node_ptr, owner)


class _ParseResult:
    """Ref-holding sentinel that frees the AST when garbage collected."""

    __slots__ = ("_node", "_parser")

    def __init__(self, node, parser):
        self._node = node
        self._parser = parser

    def __del__(self):
        if self._node != ffi.NULL:
            lib.cmark_node_free(self._node)
            self._node = ffi.NULL
        if self._parser != ffi.NULL:
            lib.cmark_parser_free(self._parser)
            self._parser = ffi.NULL
