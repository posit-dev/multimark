#ifndef CMARK_GFM_TEXMATH_H
#define CMARK_GFM_TEXMATH_H

// Named texmath.h rather than math.h so it can't shadow the C library header.

#include "cmark-gfm-core-extensions.h"

extern cmark_node_type CMARK_NODE_MATH;
cmark_syntax_extension *create_math_extension(void);

#endif
