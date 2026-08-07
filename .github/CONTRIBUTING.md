# Contributing to multimark

Thank you for your interest in contributing to multimark! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion for improvement:

1. Check if the issue already exists in the [issue tracker](https://github.com/posit-dev/multimark/issues)
2. If not, create a new issue with a clear description
3. Include steps to reproduce (for bugs) or use cases (for features)

### Submitting Pull Requests

1. Fork the repository
2. Create a new branch for your changes: `git checkout -b feature/your-feature-name`
3. Make your changes and commit them with clear, descriptive messages
4. Add tests for new functionality
5. Ensure all tests pass: `pytest`
6. Push to your fork and submit a pull request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/multimark.git
cd multimark

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with test dependencies
pip install -e .
pip install pytest

# Run tests
pytest tests/ -v
```

Note: Building from source requires a C compiler (for the cmark-gfm CFFI bindings). On most systems this is already available, but on Windows you may need the Visual Studio Build Tools.

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add NumPy-style docstrings to public functions and classes
- Keep functions focused and concise

### Running the Documentation Site

```bash
pip install great-docs
great-docs build
great-docs preview
```

### Testing Release Builds

Before cutting a release, you can dry-run each part of the build pipeline using manually triggered workflows. These mirror the release CI but don't publish anything.

From the GitHub Actions tab (or via `gh workflow run`):

- **Test Wheel Build** (`test-build.yml`): builds native abi3 wheels on Linux, macOS, and Windows
- **Test Pyodide Build** (`pyodide.yml`): builds the emscripten/WASM wheel for Pyodide
- **Test Sdist Build** (`test-sdist.yml`): builds the source distribution

```bash
# Run all three in parallel
gh workflow run test-build.yml
gh workflow run pyodide.yml
gh workflow run test-sdist.yml
```

You can also build the Pyodide wheel locally (requires Linux or macOS):

```bash
make dist-pyodide
```

## Questions?

Feel free to open an issue for questions or discussions about contributing.
