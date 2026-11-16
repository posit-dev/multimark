// multimark addition: TeX math between dollar signs, `$...$` (inline) and
// `$$...$$` (display), following Pandoc's tex_math_dollars rules
// (Text.Pandoc.Parsing.Math, pandoc 3.13+):
//
// - An inline opener can't be followed by whitespace, and an inline closer
//   can't be preceded by whitespace or followed by a digit, so `$5 and $10`
//   stays text.
// - Display math may have whitespace just inside its delimiters.
// - A backslash escapes the next character, so `\$` doesn't close the math.
// - TeX groups `{...}` and `%` comments are consumed whole, so delimiters
//   inside them (as in `\text{$x$}`) don't close the math.
// - Math can't contain a blank line, and leading and trailing whitespace is
//   trimmed from the TeX.
//
// Matching is purely inline, so a math span can't cross a block boundary:
// a `$$` span over several lines ends early if one of its lines would start a
// new block (a list item, a heading, ...).
//
// A math node holds its TeX in a single text child that belongs to this
// extension, so every renderer emits the TeX verbatim.

#include "texmath.h"
#include <parser.h>
#include <render.h>
#include <html.h>
#include <houdini.h>
#include <utf8.h>
#include <cmark_ctype.h>

cmark_node_type CMARK_NODE_MATH;

static cmark_node_internal_flags CMARK_NODE__MATH_DISPLAY;

typedef struct {
  const unsigned char *data;
  bufsize_t len;
  bufsize_t pos;
  bool dollar; // single-dollar (inline) delimiters
  cmark_strbuf *buf;
} scanner;

static bool is_ws(unsigned char c) {
  return c == ' ' || c == '\t' || c == '\n' || c == '\r';
}

// Length of the line ending at `pos` ("\n", "\r\n" or "\r"), or 0.
static bufsize_t newline_len(scanner *s, bufsize_t pos) {
  if (pos >= s->len)
    return 0;
  if (s->data[pos] == '\n')
    return 1;
  if (s->data[pos] == '\r')
    return (pos + 1 < s->len && s->data[pos + 1] == '\n') ? 2 : 1;
  return 0;
}

static bool at_blankline(scanner *s, bufsize_t pos) {
  while (pos < s->len && (s->data[pos] == ' ' || s->data[pos] == '\t'))
    pos++;
  return newline_len(s, pos) > 0;
}

static bool at_closer(scanner *s) {
  if (s->pos >= s->len || s->data[s->pos] != '$')
    return false;
  return s->dollar || (s->pos + 1 < s->len && s->data[s->pos + 1] == '$');
}

static bool at_dollar(scanner *s) {
  return s->pos < s->len && s->data[s->pos] == '$';
}

// Consume a line ending (normalized to "\n") that isn't followed by a blank
// line. Returns false if there is no line ending or the next line is blank.
static bool scan_newline(scanner *s) {
  bufsize_t nl = newline_len(s, s->pos);
  if (nl == 0 || at_blankline(s, s->pos + nl))
    return false;
  s->pos += nl;
  cmark_strbuf_putc(s->buf, '\n');
  return true;
}

// Any character, but a line ending only if the next line isn't blank.
static bool scan_char(scanner *s) {
  if (s->pos >= s->len)
    return false;
  if (newline_len(s, s->pos))
    return scan_newline(s);
  cmark_strbuf_putc(s->buf, s->data[s->pos++]);
  return true;
}

// `%` up to and including the end of the line.
static bool scan_comment(scanner *s) {
  cmark_strbuf_putc(s->buf, s->data[s->pos++]);
  while (s->pos < s->len) {
    if (newline_len(s, s->pos))
      return scan_newline(s);
    cmark_strbuf_putc(s->buf, s->data[s->pos++]);
  }
  return false;
}

// A balanced `{...}` group; escaped braces don't count.
static bool scan_group(scanner *s) {
  int depth = 1;
  bool escaped = false;

  cmark_strbuf_putc(s->buf, s->data[s->pos++]);
  while (depth > 0) {
    unsigned char c;
    if (escaped) {
      if (!scan_char(s))
        return false;
      escaped = false;
      continue;
    }
    if (s->pos < s->len && s->data[s->pos] == '%') {
      if (!scan_comment(s))
        return false;
      continue;
    }
    c = s->pos < s->len ? s->data[s->pos] : 0;
    if (!scan_char(s))
      return false;
    if (c == '\\')
      escaped = true;
    else if (c == '}')
      depth--;
    else if (c == '{')
      depth++;
  }
  return true;
}

// Scan the TeX after an opener up to and including the closer, appending it
// to s->buf. Returns false if the math isn't closed.
static bool scan_math(scanner *s) {
  if (at_closer(s))
    return false;

  do {
    unsigned char c;
    if (s->pos >= s->len)
      return false;
    c = s->data[s->pos];

    if (c == '%') {
      if (!scan_comment(s))
        return false;
    } else if (c == '{') {
      if (!scan_group(s))
        return false;
    } else if (c == ' ' || c == '\t') {
      bufsize_t start = s->pos;
      while (s->pos < s->len &&
             (s->data[s->pos] == ' ' || s->data[s->pos] == '\t'))
        s->pos++;
      if (s->dollar && at_dollar(s))
        return false;
      cmark_strbuf_put(s->buf, s->data + start, s->pos - start);
    } else if (newline_len(s, s->pos)) {
      if (!scan_newline(s) || (s->dollar && at_dollar(s)))
        return false;
    } else if (c == '\\') {
      cmark_strbuf_putc(s->buf, c);
      s->pos++;
      if (!scan_char(s))
        return false;
    } else {
      cmark_strbuf_putc(s->buf, c);
      s->pos++;
    }
  } while (!at_closer(s));

  s->pos += s->dollar ? 1 : 2;
  return true;
}

// Drop leading whitespace, and trailing whitespace except for one character
// directly after a backslash (a TeX control space such as `\ `).
static void trim_math(cmark_strbuf *buf) {
  bufsize_t end = buf->size;
  bufsize_t start = 0;

  while (end > 0 && is_ws(buf->ptr[end - 1]))
    end--;
  if (end < buf->size && end > 0 && buf->ptr[end - 1] == '\\')
    end++;
  cmark_strbuf_truncate(buf, end);

  while (start < buf->size && is_ws(buf->ptr[start]))
    start++;
  cmark_strbuf_drop(buf, start);
}

static bool starts_with_space(scanner *s) {
  int32_t uc;
  int len = cmark_utf8proc_iterate(s->data + s->pos, s->len - s->pos, &uc);
  return len > 0 && (cmark_utf8proc_is_space(uc) || uc == '\v');
}

static cmark_node *match(cmark_syntax_extension *self, cmark_parser *parser,
                         cmark_node *parent, unsigned char character,
                         cmark_inline_parser *inline_parser) {
  cmark_chunk *chunk;
  cmark_strbuf buf;
  cmark_node *math, *tex;
  scanner s;
  bufsize_t start, delim_len;
  bool display;
  int line, column;

  if (character != '$')
    return NULL;

  chunk = cmark_inline_parser_get_chunk(inline_parser);
  start = cmark_inline_parser_get_offset(inline_parser);
  display = start + 1 < chunk->len && chunk->data[start + 1] == '$';
  delim_len = display ? 2 : 1;

  cmark_strbuf_init(parser->mem, &buf, 0);
  s.data = chunk->data;
  s.len = chunk->len;
  s.pos = start + delim_len;
  s.dollar = !display;
  s.buf = &buf;

  if ((s.dollar && s.pos < s.len && starts_with_space(&s)) ||
      !scan_math(&s) ||
      (s.dollar && s.pos < s.len && cmark_isdigit(s.data[s.pos]))) {
    cmark_strbuf_free(&buf);
    return NULL;
  }
  trim_math(&buf);

  line = cmark_inline_parser_get_line(inline_parser);
  column = cmark_inline_parser_get_column(inline_parser);

  math = cmark_node_new_with_mem_and_ext(CMARK_NODE_MATH, parser->mem, self);
  if (display)
    math->flags |= CMARK_NODE__MATH_DISPLAY;

  tex = cmark_node_new_with_mem_and_ext(CMARK_NODE_TEXT, parser->mem, self);
  tex->as.literal = cmark_chunk_buf_detach(&buf);
  cmark_node_append_child(math, tex);

  cmark_inline_parser_set_offset_multiline(inline_parser, s.pos);

  math->start_line = tex->start_line = line;
  math->start_column = column;
  tex->start_column = column + delim_len;
  math->end_line = tex->end_line = cmark_inline_parser_get_line(inline_parser);
  math->end_column = cmark_inline_parser_get_column(inline_parser) - 1;
  tex->end_column = math->end_column - delim_len;

  return math;
}

static bool is_display(cmark_node *node) {
  return (node->flags & CMARK_NODE__MATH_DISPLAY) != 0;
}

bool cmark_gfm_extensions_get_math_display(cmark_node *node) {
  if (!node || !node->extension || node->type != CMARK_NODE_MATH)
    return false;
  return is_display(node);
}

static const char *get_type_string(cmark_syntax_extension *extension,
                                   cmark_node *node) {
  if (node->type == CMARK_NODE_MATH)
    return "math";
  if (node->type == CMARK_NODE_TEXT)
    return "text";
  return "<unknown>";
}

static int can_contain(cmark_syntax_extension *extension, cmark_node *node,
                       cmark_node_type child_type) {
  return node->type == CMARK_NODE_MATH && child_type == CMARK_NODE_TEXT;
}

static const char *dollars(cmark_node *node) {
  return is_display(node) ? "$$" : "$";
}

static void commonmark_render(cmark_syntax_extension *extension,
                              cmark_renderer *renderer, cmark_node *node,
                              cmark_event_type ev_type, int options) {
  if (node->type == CMARK_NODE_MATH)
    renderer->out(renderer, node, dollars(node), false, LITERAL);
  else
    renderer->out(renderer, node, cmark_node_get_literal(node), false, LITERAL);
}

static void latex_render(cmark_syntax_extension *extension,
                         cmark_renderer *renderer, cmark_node *node,
                         cmark_event_type ev_type, int options) {
  bool entering = (ev_type == CMARK_EVENT_ENTER);
  if (node->type == CMARK_NODE_MATH) {
    if (is_display(node))
      renderer->out(renderer, node, entering ? "\\[" : "\\]", false, LITERAL);
    else
      renderer->out(renderer, node, entering ? "\\(" : "\\)", false, LITERAL);
  } else {
    renderer->out(renderer, node, cmark_node_get_literal(node), false, LITERAL);
  }
}

// man and plaintext can't typeset math, so they show the TeX between its
// dollar delimiters (as Pandoc does when it can't convert the TeX).
static void man_render(cmark_syntax_extension *extension,
                       cmark_renderer *renderer, cmark_node *node,
                       cmark_event_type ev_type, int options) {
  if (node->type == CMARK_NODE_MATH)
    renderer->out(renderer, node, dollars(node), false, LITERAL);
  else
    renderer->out(renderer, node, cmark_node_get_literal(node), false, NORMAL);
}

static void plaintext_render(cmark_syntax_extension *extension,
                             cmark_renderer *renderer, cmark_node *node,
                             cmark_event_type ev_type, int options) {
  if (node->type == CMARK_NODE_MATH)
    renderer->out(renderer, node, dollars(node), false, LITERAL);
  else
    renderer->out(renderer, node, cmark_node_get_literal(node), false, LITERAL);
}

// The markup MathJax and KaTeX look for (Pandoc's --mathjax output).
static void html_render(cmark_syntax_extension *extension,
                        cmark_html_renderer *renderer, cmark_node *node,
                        cmark_event_type ev_type, int options) {
  bool entering = (ev_type == CMARK_EVENT_ENTER);
  if (node->type == CMARK_NODE_MATH) {
    if (is_display(node))
      cmark_strbuf_puts(renderer->html, entering
                                            ? "<span class=\"math display\">\\["
                                            : "\\]</span>");
    else
      cmark_strbuf_puts(renderer->html, entering
                                            ? "<span class=\"math inline\">\\("
                                            : "\\)</span>");
  } else {
    houdini_escape_html0(renderer->html, node->as.literal.data,
                         node->as.literal.len, 0);
  }
}

static const char *xml_attr(cmark_syntax_extension *extension,
                            cmark_node *node) {
  if (node->type != CMARK_NODE_MATH)
    return NULL;
  return is_display(node) ? " type=\"display\"" : " type=\"inline\"";
}

// Mark the document so the CommonMark renderer escapes literal dollars.
static cmark_node *postprocess(cmark_syntax_extension *ext,
                               cmark_parser *parser, cmark_node *root) {
  root->flags |= CMARK_NODE__ESCAPE_DOLLARS;
  return root;
}

cmark_syntax_extension *create_math_extension(void) {
  cmark_syntax_extension *ext = cmark_syntax_extension_new("math");
  cmark_llist *special_chars = NULL;

  cmark_syntax_extension_set_get_type_string_func(ext, get_type_string);
  cmark_syntax_extension_set_can_contain_func(ext, can_contain);
  cmark_syntax_extension_set_commonmark_render_func(ext, commonmark_render);
  cmark_syntax_extension_set_latex_render_func(ext, latex_render);
  cmark_syntax_extension_set_man_render_func(ext, man_render);
  cmark_syntax_extension_set_html_render_func(ext, html_render);
  cmark_syntax_extension_set_plaintext_render_func(ext, plaintext_render);
  cmark_syntax_extension_set_xml_attr_func(ext, xml_attr);
  cmark_syntax_extension_set_postprocess_func(ext, postprocess);
  CMARK_NODE_MATH = cmark_syntax_extension_add_node(1);
  cmark_register_node_flag(&CMARK_NODE__MATH_DISPLAY);

  cmark_syntax_extension_set_match_inline_func(ext, match);

  cmark_mem *mem = cmark_get_default_mem_allocator();
  special_chars = cmark_llist_append(mem, special_chars, (void *)'$');
  cmark_syntax_extension_set_special_inline_chars(ext, special_chars);

  return ext;
}
