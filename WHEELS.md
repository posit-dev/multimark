# Wheel Builds

multimark is a compiled Python package (CFFI bindings to vendored cmark-gfm C sources). Pre-built wheels are published to PyPI on each release. This document describes what gets built, for which platforms, and why.

## Python Version Support

multimark uses the Python stable ABI (abi3) with a floor of **CPython 3.9**. A single wheel per platform covers all Python versions from 3.9 onward, including future releases. The test suite runs on Python 3.9 through 3.14.

## Native Wheels

Built with cibuildwheel using the `cp39-abi3` tag.

| Platform | Architectures | Wheel tag |
|----------|--------------|-----------|
| Linux (manylinux/musllinux) | x86_64, aarch64 | `cp39-abi3-manylinux_*_{x86_64,aarch64}`, `cp39-abi3-musllinux_*_{x86_64,aarch64}` |
| macOS | x86_64, arm64 | `cp39-abi3-macosx_*_x86_64`, `cp39-abi3-macosx_*_arm64` |
| Windows | x86_64 | `cp39-abi3-win_amd64` |

Linux aarch64 wheels are built and tested under QEMU on the x86_64 GitHub Actions runner.

Skipped: 32-bit Windows (`win32`), 32-bit Linux (`manylinux_i686`), musl 32-bit (`musllinux_i686`).

## Pyodide / WebAssembly Wheels

Built with cibuildwheel using `CIBW_PLATFORM=pyodide`. These allow multimark to run in browser-based Python environments (Pyodide, JupyterLite, Shinylive).

| Pyodide Version | Python | Emscripten | Wheel tag |
|----------------|--------|------------|-----------|
| 0.29.x | 3.13 | 4.0.9 | `cp39-abi3-pyodide_2025_0_wasm32` |

Threading and CLI tests are skipped under Pyodide (emscripten does not support pthreads or subprocesses).

## Source Distribution

An sdist (`multimark-*.tar.gz`) is also published. Building from source requires a C compiler and the vendored cmark-gfm sources (included in the tarball).

## Building Locally

| Target | Command |
|--------|---------|
| Native wheel | `make dist-wheel` |
| Pyodide wheel | `make dist-pyodide` |
| Source distribution | `make dist-sdist` |
| All of the above | `make dist-all` |

## Testing Builds Before a Release

Three manually triggered GitHub Actions workflows mirror the release pipeline without publishing:

- **Test Wheel Build** (`test-build.yml`): native abi3 wheels on all platforms
- **Test Pyodide Build** (`pyodide.yml`): emscripten/WASM wheels
- **Test Sdist Build** (`test-sdist.yml`): source distribution

```bash
gh workflow run test-build.yml
gh workflow run pyodide.yml
gh workflow run test-sdist.yml
```

## Configuration

All cibuildwheel settings live in `pyproject.toml` under `[tool.cibuildwheel]`. The release CI workflow (`ci.yml`) and local Makefile targets read from the same configuration.
