from __future__ import annotations

from typing import List, Optional, Sequence

from multimark._binding import ffi, lib
from multimark._cmark import _build_options


def _render_html_chunk(encoded: Sequence[bytes], opts: int) -> List[str]:
    """Render a chunk of pre-encoded documents in a single C batch call.

    The whole parse+render+free loop runs in C, so the GIL is released once for
    the entire chunk rather than once per document.
    """
    n = len(encoded)
    if n == 0:
        return []

    # Zero-copy views into the Python bytes; keep them alive for the call.
    inputs = ffi.new("char*[]", n)
    lens = ffi.new("size_t[]", n)
    for i, buf in enumerate(encoded):
        inputs[i] = ffi.from_buffer(buf)
        lens[i] = len(buf)

    outputs = ffi.new("char*[]", n)
    rendered = lib.mm_render_html_batch(inputs, lens, n, opts, outputs)

    try:
        if rendered < 0:
            raise MemoryError("Failed to render document batch")
        return [ffi.string(outputs[i]).decode("utf-8") for i in range(n)]
    finally:
        for i in range(n):
            if outputs[i] != ffi.NULL:
                lib.free(outputs[i])


def markdown_to_html_batch(
    texts: Sequence[str],
    *,
    hardbreaks: bool = False,
    smart: bool = False,
    normalize: bool = False,
    sourcepos: bool = False,
    unsafe: bool = False,
    footnotes: bool = False,
    options: int = 0,
    workers: Optional[int] = None,
) -> List[str]:
    """Render many Markdown documents to HTML in one call.

    Equivalent to `[markdown_to_html(t, ...) for t in texts]` but faster: the
    parse/render/free loop happens in C, cutting per-document Python overhead,
    and the GIL is released for the whole batch. Set `workers` above 1 to fan
    the batch across threads for real multi-core parallelism (the C work runs
    with the GIL released, so threads scale).

    Parameters
    ----------
    texts
        The Markdown documents to render. Each must be a `str`.
    workers
        Number of worker threads. `None` or `1` renders the whole batch in a
        single C call on the current thread. A value `> 1` splits the batch
        into that many chunks rendered concurrently.
    options, smart, unsafe, ...
        Same parsing/rendering options as :func:`markdown_to_html`. GFM
        `extensions=` are not yet supported by the batch path.

    Returns
    -------
    list[str]
        Rendered HTML, in the same order as `texts`.
    """
    opts = _build_options(
        options, hardbreaks, smart, normalize, sourcepos, unsafe, footnotes
    )
    encoded = [t.encode("utf-8") for t in texts]
    n = len(encoded)

    if n == 0:
        return []

    if workers is None or workers <= 1 or n == 1:
        return _render_html_chunk(encoded, opts)

    import concurrent.futures as cf

    workers = min(workers, n)
    # Contiguous chunks preserve order when reassembled.
    chunk_size = (n + workers - 1) // workers
    chunks = [encoded[i : i + chunk_size] for i in range(0, n, chunk_size)]

    results: List[List[str]] = [[]] * len(chunks)
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(_render_html_chunk, chunk, opts): idx
            for idx, chunk in enumerate(chunks)
        }
        for fut in cf.as_completed(futures):
            results[futures[fut]] = fut.result()

    out: List[str] = []
    for part in results:
        out.extend(part)
    return out
