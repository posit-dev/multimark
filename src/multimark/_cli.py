from __future__ import annotations

import click

from multimark import (
    __version__,
    markdown_to_html,
    markdown_to_latex,
    markdown_to_man,
    markdown_to_commonmark,
    markdown_to_xml,
    VALID_EXTENSIONS,
)

RENDERERS = {
    "html": markdown_to_html,
    "latex": markdown_to_latex,
    "man": markdown_to_man,
    "commonmark": markdown_to_commonmark,
    "xml": markdown_to_xml,
}


@click.command()
@click.argument("file", type=click.File("r"), default="-")
@click.option(
    "-t",
    "--to",
    "format",
    type=click.Choice(list(RENDERERS.keys()), case_sensitive=False),
    default="html",
    help="Output format.",
)
@click.option(
    "-o",
    "--output",
    type=click.File("w"),
    default="-",
    help="Output file (stdout if omitted).",
)
@click.option(
    "-e",
    "--extension",
    "extensions",
    multiple=True,
    type=click.Choice(sorted(VALID_EXTENSIONS), case_sensitive=False),
    help="Enable a GFM extension (repeatable).",
)
@click.option("--smart", is_flag=True, help="Use smart punctuation.")
@click.option("--unsafe", is_flag=True, help="Allow raw HTML and dangerous URLs.")
@click.option("--hardbreaks", is_flag=True, help="Render softbreaks as hard line breaks.")
@click.option("--sourcepos", is_flag=True, help="Include source position attributes (html/xml only).")
@click.option("--footnotes", is_flag=True, help="Enable footnote parsing.")
@click.option("--width", type=int, default=0, help="Wrap output at this column width (latex/man/commonmark only).")
@click.version_option(__version__, prog_name="multimark")
def main(
    file,
    format: str,
    output,
    extensions: tuple[str, ...],
    smart: bool,
    unsafe: bool,
    hardbreaks: bool,
    sourcepos: bool,
    footnotes: bool,
    width: int,
) -> None:
    """Convert CommonMark/GFM Markdown to various output formats.

    Reads Markdown from FILE (or stdin if omitted) and writes the converted
    output to stdout or the file specified by --output.
    """
    text = file.read()

    renderer = RENDERERS[format]
    kwargs: dict = dict(
        extensions=list(extensions) or None,
        smart=smart,
        unsafe=unsafe,
        hardbreaks=hardbreaks,
        footnotes=footnotes,
    )

    # sourcepos is only supported by html and xml renderers
    if format in ("html", "xml"):
        kwargs["sourcepos"] = sourcepos

    # width is only supported by latex, man, and commonmark renderers
    if format in ("latex", "man", "commonmark"):
        kwargs["width"] = width

    result = renderer(text, **kwargs)
    output.write(result)
