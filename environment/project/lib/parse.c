#include <string.h>
#include "record.h"
#include "parse_internal.h"

static int level_of(const char *word, size_t len)
{
    if (len == 4 && strncmp(word, "INFO", 4) == 0)
        return LVL_INFO;
    if (len == 4 && strncmp(word, "WARN", 4) == 0)
        return LVL_WARN;
    if (len == 5 && strncmp(word, "ERROR", 5) == 0)
        return LVL_ERROR;
    return LVL_UNKNOWN;
}

int parse_line(const char *line, int line_no, struct record *out)
{
    const char *p = skip_spaces(line);
    const char *w = p;
    size_t n;

    if (*p == '\n' || *p == '\0')
        return -1;
    while (*p && *p != ' ' && *p != '\t' && *p != '\n')
        p++;
    out->level = level_of(w, (size_t)(p - w));
    out->line_no = line_no;
    p = skip_spaces(p);
    n = strcspn(p, "\n");
    if (n >= MSG_MAX)
        n = MSG_MAX - 1;
    memcpy(out->msg, p, n);
    out->msg[n] = '\0';
    return 0;
}
