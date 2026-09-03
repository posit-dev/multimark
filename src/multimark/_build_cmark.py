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

    /* Batch HTML renderer: parse + render + free a whole array of documents
       in a single C loop. Because this is one cffi boundary crossing, the GIL
       is released for the entire batch rather than once per document, and the
       per-document Python-side dispatch overhead disappears. Each outputs[i]
       is a malloc'd C string the caller frees; on failure returns -1 and any
       already-rendered outputs[i] are non-NULL for the caller to free. */
    int mm_render_html_batch(const char **inputs, size_t *lens, size_t n,
                             int options, char **outputs) {
        size_t i;
        for (i = 0; i < n; i++) {
            outputs[i] = (char *)0;
        }
        for (i = 0; i < n; i++) {
            cmark_node *node = cmark_parse_document(inputs[i], lens[i], options);
            if (node == (cmark_node *)0) {
                return -1;
            }
            char *html = cmark_render_html(node, options, (cmark_llist *)0);
            cmark_node_free(node);
            if (html == (char *)0) {
                return -1;
            }
            outputs[i] = html;
        }
        return (int)n;
    }
    """,
    sources=src_sources + ext_sources,
    include_dirs=[src_dir_abs, ext_dir_abs],
    define_macros=[("CMARK_GFM_STATIC_DEFINE", None)],
)

if __name__ == "__main__":
    ffi.compile(verbose=True)
