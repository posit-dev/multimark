from multimark import markdown_to_html, markdown_to_html_batch


DOCS = [
    "# Heading\n\nA paragraph with **bold** and *italic*.\n",
    "text with a [link](http://example.com) and `code`",
    "",
    "plain line",
    "<div>raw html</div>",
    "- one\n- two\n- three\n",
]


def _ref(docs, **kw):
    return [markdown_to_html(d, **kw) for d in docs]


def test_batch_matches_per_call():
    assert markdown_to_html_batch(DOCS) == _ref(DOCS)


def test_batch_empty():
    assert markdown_to_html_batch([]) == []


def test_batch_single():
    assert markdown_to_html_batch(["**hi**"]) == [markdown_to_html("**hi**")]


def test_batch_options_parity():
    for kw in ({"smart": True}, {"unsafe": True}, {"sourcepos": True}):
        assert markdown_to_html_batch(DOCS, **kw) == _ref(DOCS, **kw), kw


def test_batch_workers_preserve_order():
    docs = [f"# Doc {i}\n\nParagraph {i}\n" for i in range(500)]
    ref = _ref(docs)
    for w in (1, 2, 4, 8):
        assert markdown_to_html_batch(docs, workers=w) == ref, w


def test_batch_workers_more_than_docs():
    assert markdown_to_html_batch(DOCS, workers=64) == _ref(DOCS)
