<p align="center">
<img src="https://posit-dev.github.io/multimark/assets/logo.png" alt="multimark" width="350">
</p>
<p align="center">
<a href="https://pypi.org/project/multimark/"><img src="https://img.shields.io/pypi/v/multimark?logo=python&logoColor=white&color=orange" alt="PyPI"></a>
<a href="https://pypi.org/project/multimark/"><img src="https://img.shields.io/pypi/pyversions/multimark.svg" alt="Python versions"></a>
<a href="https://pypistats.org/packages/multimark"><img src="https://img.shields.io/pypi/dm/multimark" alt="Downloads"></a>
<a href="https://choosealicense.com/licenses/mit/"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License"></a>
<a href="https://github.com/posit-dev/multimark/actions/workflows/ci.yml"><img src="https://github.com/posit-dev/multimark/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
</p>

The **multimark** package has Python bindings to [cmark-gfm](https://github.com/github/cmark-gfm), the C reference implementation of [CommonMark](https://commonmark.org/) with GitHub Flavored Markdown extensions.

Renders Markdown to **HTML**, **LaTeX**, **groff man**, **XML**, **normalized CommonMark**, and **plain text**: all from a single, lightweight package.

## Installation

```bash
pip install multimark
```

Wheels are available for Linux, macOS, and Windows (Python 3.9+). No system dependencies required.

## Quick Start

```python
from multimark import markdown_to_html, markdown_to_latex

html = markdown_to_html("**Hello**, *world*!")
# '<p><strong>Hello</strong>, <em>world</em>!</p>\n'

latex = markdown_to_latex("**Hello**, *world*!")
# '\\textbf{Hello}, \\emph{world}!\n'
```

## Renderers

| Function | Output Format |
|----------|---------------|
| `markdown_to_html()` | HTML |
| `markdown_to_latex()` | LaTeX |
| `markdown_to_man()` | groff man page |
| `markdown_to_commonmark()` | Normalized CommonMark |
| `markdown_to_plaintext()` | Readable plain text |
| `markdown_to_xml()` | XML (AST representation) |

```python
from multimark import markdown_to_plaintext

markdown_to_plaintext("**Hello**, *world*!")
# 'Hello, world!\n'
```

Plaintext output preserves list markers, code contents, and image descriptions,
but drops link destinations. GFM tables keep pipe syntax, task lists keep checkbox
markers, and strikethrough uses single tildes. Raw HTML blocks (including their
text) are omitted even with `unsafe=True`. Empty input returns `"\n"`.

## Options

Use named boolean keyword arguments for common settings:

```python
from multimark import markdown_to_html, markdown_to_latex

# Smart punctuation (curly quotes, em-dashes)
markdown_to_html('"Hello" -- world...', smart=True)
# '<p>\u201cHello\u201d \u2013 world\u2026</p>\n'

# Allow raw HTML passthrough (safe mode is the default)
markdown_to_html('<div>hi</div>', unsafe=True)
# '<div>hi</div>\n'

# Source position attributes
markdown_to_html('**Hello**', sourcepos=True)
# '<p data-sourcepos="1:1-1:9"><strong>Hello</strong></p>\n'

# Line wrapping (LaTeX, man, CommonMark, and plaintext renderers)
markdown_to_latex('**Hello**, *world*!', width=80)
# '\\textbf{Hello}, \\emph{world}!\n'

# Footnotes
markdown_to_html('Text[^1]\n\n[^1]: A footnote\n', footnotes=True)
# '<p>Text<sup class="footnote-ref">...</sup></p>\n<section class="footnotes">...\n'
```

Or compose flags with the `Options` bitmask:

```python
from multimark import markdown_to_html, Options

html = markdown_to_html(text, options=Options.SMART | Options.UNSAFE)
```

## GFM Extensions

Enable GitHub Flavored Markdown extensions by name:

```python
from multimark import markdown_to_html

# Tables
markdown_to_html('| A | B |\n|---|---|\n| 1 | 2 |\n', extensions=["table"])
# '<table>\n<thead>\n<tr>\n<th>A</th>\n<th>B</th>\n</tr>...\n'

# Strikethrough
markdown_to_html('~~deleted~~', extensions=["strikethrough"])
# '<p><del>deleted</del></p>\n'

# Multiple extensions
html = markdown_to_html(text, extensions=["table", "strikethrough", "autolink", "tasklist", "tagfilter"])
```

Available extensions: `table`, `strikethrough`, `autolink`, `tagfilter`, `tasklist`.

## All Renderer Parameters

Every renderer accepts:

- **`text`**: Markdown string
- **`options`**: raw bitmask (default `0`)
- **`extensions`**: list of GFM extension names (default `()`)
- **`smart`**: smart punctuation
- **`hardbreaks`**: render soft breaks as `<br>`
- **`unsafe`**: allow raw HTML (no effect on plaintext output)
- **`normalize`**: consolidate adjacent text nodes
- **`footnotes`**: enable footnote syntax

Additional parameters:

- **`sourcepos`**: Source position attributes (HTML and XML only)
- **`width`**: Line wrap column (LaTeX, man, CommonMark, and plaintext only; `0` = no wrap)

For plaintext, `hardbreaks=True` disables width-based wrapping. With `width=0`,
soft line breaks are preserved; a positive width reflows them as spaces before
wrapping. Output whitespace and trailing newlines are retained.

## Why multimark?

Several Python packages wrap cmark or provide CommonMark parsing. Here's how they compare:

| | **multimark** | **[cmarkgfm](https://github.com/theacodes/cmarkgfm)** | **[commonmark.py](https://github.com/readthedocs/commonmark.py)** |
|---|---|---|---|
| Engine | cmark-gfm (C, vendored) | cmark-gfm (C, vendored) | Pure Python |
| Output formats | HTML, LaTeX, man, XML, CommonMark, plaintext | HTML only | HTML only |
| GFM extensions | ✓ | ✓ | ✗ |
| Safe by default | ✓ | ✓ | ✗ |
| Convenience kwargs | `smart=True`, `unsafe=True`, etc. | Raw bitmask only | N/A |
| Performance | **Fastest** (14% faster than cmarkgfm) | Fast | ~31× slower |
| Maintained | Active (2026) | Active (2025) | Unmaintained (2019) |

multimark uses the same battle-tested C library as `cmarkgfm` but exposes all six of cmark's output formats (not just HTML). The API is designed around keyword arguments rather than opaque bitmasks, and unsafe content is blocked by default so the safe choice requires no extra configuration.

Thanks to extension pointer caching and reduced Python-side overhead, multimark is the **fastest Python Markdown-to-HTML library**. Take a look at the [benchmarks](https://posit-dev.github.io/multimark/user-guide/performance.html) for more detail on this.

## License

MIT and BSD-2-Clause (`cmark-gfm`).
