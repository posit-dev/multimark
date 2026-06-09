import pytest

from multimark import markdown_to_html, Options
from spec_parser import load_fixtures

# Load all fixture files
SPEC_EXAMPLES = load_fixtures("spec.txt", "regression.txt")
SMART_EXAMPLES = load_fixtures("smart_punct.txt")


def _example_id(example):
    """Generate a readable test ID."""
    return f"{example.fixture_file}::ex{example.example}::{example.section}"


@pytest.mark.parametrize("example", SPEC_EXAMPLES, ids=_example_id)
def test_spec_html(example):
    """Verify HTML output matches the CommonMark spec.

    The spec assumes raw HTML passes through (UNSAFE mode), which is the
    standard way to run the spec tests per cmark's own test runner.
    """
    result = markdown_to_html(
        example.markdown, options=Options.VALIDATE_UTF8 | Options.UNSAFE
    )
    assert result == example.html, (
        f"Example {example.example} ({example.section}) "
        f"at {example.fixture_file}:{example.start_line}\n"
        f"Input:\n{example.markdown!r}\n"
        f"Expected:\n{example.html!r}\n"
        f"Got:\n{result!r}"
    )


@pytest.mark.parametrize("example", SMART_EXAMPLES, ids=_example_id)
def test_smart_punct_html(example):
    """Verify smart punctuation rendering."""
    result = markdown_to_html(
        example.markdown, options=Options.SMART | Options.VALIDATE_UTF8
    )
    assert result == example.html, (
        f"Example {example.example} ({example.section}) "
        f"at {example.fixture_file}:{example.start_line}\n"
        f"Input:\n{example.markdown!r}\n"
        f"Expected:\n{example.html!r}\n"
        f"Got:\n{result!r}"
    )
