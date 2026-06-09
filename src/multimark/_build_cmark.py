import os
import glob
from cffi import FFI

ffi = FFI()

here = os.path.dirname(os.path.abspath(__file__))

# Read the CFFI declarations
with open(os.path.join(here, "cmark.cffi.h")) as f:
    ffi.cdef(f.read())

# Locate vendored cmark-gfm C sources (use relative paths from project root for setuptools)
project_root = os.path.normpath(os.path.join(here, "..", ".."))
src_dir_abs = os.path.join(project_root, "third_party", "cmark-gfm", "src")
ext_dir_abs = os.path.join(project_root, "third_party", "cmark-gfm", "extensions")
src_dir_rel = os.path.join("third_party", "cmark-gfm", "src")
ext_dir_rel = os.path.join("third_party", "cmark-gfm", "extensions")

# Core library sources (exclude main.c)
src_sources_abs = sorted(glob.glob(os.path.join(src_dir_abs, "*.c")))
src_sources = [
    os.path.join(src_dir_rel, os.path.basename(s))
    for s in src_sources_abs
    if not s.endswith("main.c")
]

# Extension sources
ext_sources_abs = sorted(glob.glob(os.path.join(ext_dir_abs, "*.c")))
ext_sources = [
    os.path.join(ext_dir_rel, os.path.basename(s))
    for s in ext_sources_abs
]

ffi.set_source(
    "multimark._binding",
    """
    #include "cmark-gfm.h"
    #include "cmark-gfm-core-extensions.h"
    """,
    sources=src_sources + ext_sources,
    include_dirs=[src_dir_abs, ext_dir_abs],
    define_macros=[("CMARK_GFM_STATIC_DEFINE", None)],
)

if __name__ == "__main__":
    ffi.compile(verbose=True)
