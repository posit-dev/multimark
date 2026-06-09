import concurrent.futures

from multimark import (
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_commonmark,
    markdown_to_xml,
)


def _render_all(doc_id: int) -> dict:
    """Render a unique document through all renderers."""
    md = f"# Document {doc_id}\n\nThis is paragraph **{doc_id}** with *emphasis*.\n"
    return {
        "id": doc_id,
        "html": markdown_to_html(md),
        "latex": markdown_to_latex(md),
        "man": markdown_to_man(md),
        "commonmark": markdown_to_commonmark(md),
        "xml": markdown_to_xml(md),
    }


def test_concurrent_rendering():
    """Multiple threads rendering simultaneously produce correct results."""
    num_docs = 200

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_render_all, i) for i in range(num_docs)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == num_docs

    # Verify each result contains its unique document ID
    for r in results:
        doc_id = r["id"]
        assert f"Document {doc_id}" in r["html"]
        assert f"{doc_id}" in r["latex"]
        assert f"{doc_id}" in r["xml"]


def test_concurrent_same_document():
    """Many threads rendering the same document produce identical output."""
    md = "# Hello\n\n**bold** and *italic* with `code`\n"
    num_threads = 100

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(markdown_to_html, md) for _ in range(num_threads)]
        results = [f.result() for f in futures]

    # All results should be identical
    assert all(r == results[0] for r in results)


def test_concurrent_mixed_renderers():
    """Different renderers called concurrently on different inputs."""
    tasks = []
    renderers = [
        markdown_to_html,
        markdown_to_latex,
        markdown_to_man,
        markdown_to_commonmark,
        markdown_to_xml,
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for i in range(500):
            renderer = renderers[i % len(renderers)]
            md = f"Item **{i}** in list\n"
            tasks.append(executor.submit(renderer, md))

        results = [t.result() for t in tasks]

    assert len(results) == 500
    assert all(isinstance(r, str) for r in results)
