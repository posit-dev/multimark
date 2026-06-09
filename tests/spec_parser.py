from __future__ import annotations

import os
import re
from dataclasses import dataclass

EXAMPLE_START = "`" * 32 + " example"
EXAMPLE_END = "`" * 32
SECTION_RE = re.compile(r"^(#{1,6}) (.+)")


@dataclass
class SpecExample:
    """A single test example from a spec-format file."""

    markdown: str
    html: str
    example: int
    section: str
    start_line: int
    end_line: int
    fixture_file: str


def parse_spec_file(filepath: str) -> list[SpecExample]:
    """Parse a CommonMark spec-format file into a list of examples."""
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    examples: list[SpecExample] = []
    section = ""
    example_num = 0
    state = 0  # 0=outside, 1=reading markdown, 2=reading html
    markdown_lines: list[str] = []
    html_lines: list[str] = []
    start_line = 0
    filename = os.path.basename(filepath)

    for i, line in enumerate(lines, start=1):
        stripped = line.rstrip("\n")

        if state == 0:
            m = SECTION_RE.match(stripped)
            if m:
                section = m.group(2)
            elif stripped == EXAMPLE_START:
                state = 1
                start_line = i
                markdown_lines = []
                html_lines = []
        elif state == 1:
            if stripped == ".":
                state = 2
            else:
                markdown_lines.append(line)
        elif state == 2:
            if stripped == EXAMPLE_END:
                example_num += 1
                markdown = "".join(markdown_lines).replace("\u2192", "\t")
                html = "".join(html_lines).replace("\u2192", "\t")
                examples.append(
                    SpecExample(
                        markdown=markdown,
                        html=html,
                        example=example_num,
                        section=section,
                        start_line=start_line,
                        end_line=i,
                        fixture_file=filename,
                    )
                )
                state = 0
            else:
                html_lines.append(line)

    return examples


def load_fixtures(*filenames: str) -> list[SpecExample]:
    """Load examples from one or more fixture files in tests/fixtures/."""
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    examples: list[SpecExample] = []
    for name in filenames:
        path = os.path.join(fixtures_dir, name)
        if os.path.exists(path):
            examples.extend(parse_spec_file(path))
    return examples
