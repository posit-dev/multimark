---
name: multimark
description: >
  Python bindings to cmark-gfm: CommonMark/GFM parsing and rendering
  (HTML, LaTeX, man, XML, CommonMark). Use when writing Python code that
  converts Markdown to other formats using the multimark package.
license: MIT
compatibility: Requires Python >=3.9.
---

# multimark

Fast Python bindings to the cmark-gfm C library for parsing CommonMark and
GitHub Flavored Markdown (GFM) into HTML, LaTeX, groff man pages, XML, or
normalized CommonMark.

## Installation

```bash
pip install multimark
```

## Decision Table

| Need | Use |
|------|-----|
| Convert Markdown to HTML | `markdown_to_html(text)` |
| Convert Markdown to LaTeX | `markdown_to_latex(text)` |
| Convert Markdown to groff man page | `markdown_to_man(text)` |
| Convert Markdown to XML AST | `markdown_to_xml(text)` |
| Normalize/reformat Markdown | `markdown_to_commonmark(text)` |
| Enable GFM tables | `markdown_to_html(text, extensions=["table"])` |
| Enable strikethrough | `markdown_to_html(text, extensions=["strikethrough"])` |
| Enable autolinks | `markdown_to_html(text, extensions=["autolink"])` |
| Enable task lists | `markdown_to_html(text, extensions=["tasklist"])` |
| Combine multiple options | `markdown_to_html(text, options=Options.SMART \| Options.UNSAFE)` |
| Check bundled cmark-gfm version | `cmark_version()` |

## API

All renderer functions share the same signature pattern:

```python
from multimark import markdown_to_html, markdown_to_latex, markdown_to_man, markdown_to_xml, markdown_to_commonmark

# Basic usage: all renderers accept the same keyword arguments
html = markdown_to_html(text, smart=True, unsafe=True, extensions=["table", "autolink"])
```

### Common keyword arguments (all renderers)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hardbreaks` | `bool` | `False` | Render soft newlines as `<br />` |
| `smart` | `bool` | `False` | Typographic quotes, en/em-dashes, ellipses |
| `normalize` | `bool` | `False` | Consolidate adjacent text nodes |
| `sourcepos` | `bool` | `False` | Add source position attributes (HTML/XML only) |
| `unsafe` | `bool` | `False` | Allow raw HTML passthrough |
| `footnotes` | `bool` | `False` | Enable `[^label]` footnote syntax |
| `extensions` | `Sequence[str]` | `()` | GFM extensions to enable |
| `options` | `int` | `0` | Bitmask of `Options` flags |

### Additional parameter (LaTeX, man, CommonMark renderers only)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `width` | `int` | `0` | Line wrap column (0 = no wrapping) |

### Options bitmask

```python
from multimark import Options

# Combine flags with |
opts = Options.SMART | Options.UNSAFE | Options.FOOTNOTES

# GFM-specific flags (no keyword shortcut)
opts = Options.GITHUB_PRE_LANG | Options.STRIKETHROUGH_DOUBLE_TILDE | Options.LIBERAL_HTML_TAG
```

### Valid GFM extensions

The only valid extension names are: `"table"`, `"strikethrough"`, `"autolink"`, `"tagfilter"`, `"tasklist"`.

## Gotchas

1. The module name is `multimark`, not `multi-mark` or `multi_mark`.
2. Raw HTML is **stripped by default** (replaced with `<!-- raw HTML omitted -->`). You must pass `unsafe=True` to allow HTML passthrough.
3. The `extensions` parameter takes a **sequence of strings**, not a single string. Use `extensions=["table"]`, never `extensions="table"`.
4. The `sourcepos` parameter is silently ignored by `markdown_to_latex()` and `markdown_to_man()` (it only affects HTML and XML output).
5. `Options` flags and keyword arguments are merged via OR. `markdown_to_html(text, smart=True, options=Options.UNSAFE)` means `SMART | UNSAFE`.
6. Passing an invalid extension name raises `ValueError`, not `KeyError`.
7. All renderers return `str`, never `bytes`. Input must also be `str`.
8. The `width` parameter is not available on `markdown_to_html()` or `markdown_to_xml()`.

## CLI

The package provides a `multimark` command (built with Click):

```bash
# Markdown from stdin to HTML on stdout (default)
echo "# Hello" | multimark

# File to HTML
multimark README.md

# Choose output format
multimark --to latex README.md
multimark --to man README.md
multimark --to xml README.md
multimark --to commonmark README.md

# Write to a file
multimark -o output.html README.md

# Enable GFM extensions (repeatable -e flag)
multimark -e table -e strikethrough README.md

# Options
multimark --smart --unsafe --hardbreaks --footnotes README.md
multimark --sourcepos README.md          # html/xml only
multimark --to latex --width 72 README.md  # latex/man/commonmark only

# Version
multimark --version
```

### CLI Options Reference

| Option | Short | Description |
|--------|-------|-------------|
| `--to FORMAT` | `-t` | Output format: `html` (default), `latex`, `man`, `commonmark`, `xml` |
| `--output FILE` | `-o` | Write to FILE instead of stdout |
| `--extension EXT` | `-e` | Enable a GFM extension (repeatable) |
| `--smart` | | Typographic quotes, dashes, ellipses |
| `--unsafe` | | Allow raw HTML passthrough |
| `--hardbreaks` | | Render soft newlines as hard line breaks |
| `--sourcepos` | | Add source position attributes (html/xml only) |
| `--footnotes` | | Enable footnote parsing |
| `--width N` | | Wrap at column N (latex/man/commonmark only; 0 = no wrap) |
| `--version` | | Show version and exit |
| `--help` | | Show help and exit |

## Best Practices

- Prefer keyword arguments (`smart=True`) over the `Options` bitmask for common flags.
- Use the `Options` bitmask only for GFM-specific flags that lack keyword shortcuts (`GITHUB_PRE_LANG`, `STRIKETHROUGH_DOUBLE_TILDE`, `LIBERAL_HTML_TAG`).
- Enable only the GFM extensions you need: each adds parsing overhead.
- For security-sensitive contexts, never set `unsafe=True`. The default safe mode strips all raw HTML.
- The library is thread-safe: you can call renderers from multiple threads concurrently.

## Resources

- [Full documentation](https://posit-dev.github.io/multimark/)
- [llms.txt](https://posit-dev.github.io/multimark/llms.txt): Indexed API reference for LLMs
- [llms-full.txt](https://posit-dev.github.io/multimark/llms-full.txt): Comprehensive documentation for LLMs
