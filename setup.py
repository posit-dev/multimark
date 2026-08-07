"""Setup script for CFFI C extension build."""
from setuptools import setup

setup(
    cffi_modules=["src/multimark/_build_cmark.py:ffi"],
    options={"bdist_wheel": {"py_limited_api": "cp39"}},
)
