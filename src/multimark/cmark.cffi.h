/* Core types */
typedef struct cmark_node cmark_node;
typedef struct cmark_parser cmark_parser;
typedef struct cmark_syntax_extension cmark_syntax_extension;
typedef struct _cmark_llist {
    struct _cmark_llist *next;
    void *data;
} cmark_llist;

/* Parser API (streaming with extension support) */
cmark_parser *cmark_parser_new(int options);
void cmark_parser_free(cmark_parser *parser);
void cmark_parser_feed(cmark_parser *parser, const char *buffer, size_t len);
cmark_node *cmark_parser_finish(cmark_parser *parser);
int cmark_parser_attach_syntax_extension(cmark_parser *parser, cmark_syntax_extension *extension);
cmark_llist *cmark_parser_get_syntax_extensions(cmark_parser *parser);

/* Simple parsing (no extensions) */
cmark_node *cmark_parse_document(const char *buffer, size_t len, int options);
void cmark_node_free(cmark_node *node);

/* Extension registration */
void cmark_gfm_core_extensions_ensure_registered(void);
cmark_syntax_extension *cmark_find_syntax_extension(const char *name);

/* Rendering */
char *cmark_render_html(cmark_node *root, int options, cmark_llist *extensions);
char *cmark_render_latex(cmark_node *root, int options, int width);
char *cmark_render_man(cmark_node *root, int options, int width);
char *cmark_render_commonmark(cmark_node *root, int options, int width);
char *cmark_render_xml(cmark_node *root, int options);

const char *cmark_version_string(void);

void free(void *ptr);

/* Tree traversal */
cmark_node *cmark_node_next(cmark_node *node);
cmark_node *cmark_node_previous(cmark_node *node);
cmark_node *cmark_node_parent(cmark_node *node);
cmark_node *cmark_node_first_child(cmark_node *node);
cmark_node *cmark_node_last_child(cmark_node *node);

/* Node type enum */
typedef enum {
    CMARK_NODE_NONE = ...,
    CMARK_NODE_DOCUMENT = ...,
    CMARK_NODE_BLOCK_QUOTE = ...,
    CMARK_NODE_LIST = ...,
    CMARK_NODE_ITEM = ...,
    CMARK_NODE_CODE_BLOCK = ...,
    CMARK_NODE_HTML_BLOCK = ...,
    CMARK_NODE_CUSTOM_BLOCK = ...,
    CMARK_NODE_PARAGRAPH = ...,
    CMARK_NODE_HEADING = ...,
    CMARK_NODE_THEMATIC_BREAK = ...,
    CMARK_NODE_FOOTNOTE_DEFINITION = ...,
    CMARK_NODE_TEXT = ...,
    CMARK_NODE_SOFTBREAK = ...,
    CMARK_NODE_LINEBREAK = ...,
    CMARK_NODE_CODE = ...,
    CMARK_NODE_HTML_INLINE = ...,
    CMARK_NODE_CUSTOM_INLINE = ...,
    CMARK_NODE_EMPH = ...,
    CMARK_NODE_STRONG = ...,
    CMARK_NODE_LINK = ...,
    CMARK_NODE_IMAGE = ...,
    CMARK_NODE_FOOTNOTE_REFERENCE = ...,
} cmark_node_type;

/* List type enum */
typedef enum {
    CMARK_NO_LIST = ...,
    CMARK_BULLET_LIST = ...,
    CMARK_ORDERED_LIST = ...,
} cmark_list_type;

/* Delimiter type enum */
typedef enum {
    CMARK_NO_DELIM = ...,
    CMARK_PERIOD_DELIM = ...,
    CMARK_PAREN_DELIM = ...,
} cmark_delim_type;

/* Event type enum */
typedef enum {
    CMARK_EVENT_NONE = ...,
    CMARK_EVENT_DONE = ...,
    CMARK_EVENT_ENTER = ...,
    CMARK_EVENT_EXIT = ...,
} cmark_event_type;

/* Node introspection */
cmark_node_type cmark_node_get_type(cmark_node *node);
const char *cmark_node_get_type_string(cmark_node *node);
const char *cmark_node_get_literal(cmark_node *node);
int cmark_node_get_heading_level(cmark_node *node);
cmark_list_type cmark_node_get_list_type(cmark_node *node);
cmark_delim_type cmark_node_get_list_delim(cmark_node *node);
int cmark_node_get_list_start(cmark_node *node);
int cmark_node_get_list_tight(cmark_node *node);
const char *cmark_node_get_fence_info(cmark_node *node);
const char *cmark_node_get_url(cmark_node *node);
const char *cmark_node_get_title(cmark_node *node);
int cmark_node_get_start_line(cmark_node *node);
int cmark_node_get_start_column(cmark_node *node);
int cmark_node_get_end_line(cmark_node *node);
int cmark_node_get_end_column(cmark_node *node);

/* Node creation and mutation */
cmark_node *cmark_node_new(cmark_node_type type);
void cmark_node_unlink(cmark_node *node);
int cmark_node_insert_before(cmark_node *node, cmark_node *sibling);
int cmark_node_insert_after(cmark_node *node, cmark_node *sibling);
int cmark_node_prepend_child(cmark_node *node, cmark_node *child);
int cmark_node_append_child(cmark_node *node, cmark_node *child);
int cmark_node_replace(cmark_node *oldnode, cmark_node *newnode);
int cmark_node_set_literal(cmark_node *node, const char *content);
int cmark_node_set_heading_level(cmark_node *node, int level);
int cmark_node_set_url(cmark_node *node, const char *url);
int cmark_node_set_title(cmark_node *node, const char *title);
int cmark_node_set_list_type(cmark_node *node, cmark_list_type type);
int cmark_node_set_list_start(cmark_node *node, int start);
int cmark_node_set_list_tight(cmark_node *node, int tight);
int cmark_node_set_fence_info(cmark_node *node, const char *info);

/* Iterator */
typedef struct cmark_iter cmark_iter;
cmark_iter *cmark_iter_new(cmark_node *root);
void cmark_iter_free(cmark_iter *iter);
cmark_event_type cmark_iter_next(cmark_iter *iter);
cmark_node *cmark_iter_get_node(cmark_iter *iter);
cmark_event_type cmark_iter_get_event_type(cmark_iter *iter);

/* Core options */
#define CMARK_OPT_DEFAULT ...
#define CMARK_OPT_SOURCEPOS ...
#define CMARK_OPT_HARDBREAKS ...
#define CMARK_OPT_SAFE ...
#define CMARK_OPT_UNSAFE ...
#define CMARK_OPT_NOBREAKS ...
#define CMARK_OPT_NORMALIZE ...
#define CMARK_OPT_VALIDATE_UTF8 ...
#define CMARK_OPT_SMART ...

/* GFM-specific options */
#define CMARK_OPT_GITHUB_PRE_LANG ...
#define CMARK_OPT_LIBERAL_HTML_TAG ...
#define CMARK_OPT_FOOTNOTES ...
#define CMARK_OPT_STRIKETHROUGH_DOUBLE_TILDE ...
#define CMARK_OPT_TABLE_PREFER_STYLE_ATTRIBUTES ...
#define CMARK_OPT_FULL_INFO_STRING ...
