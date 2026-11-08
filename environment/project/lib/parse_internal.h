#ifndef PARSE_INTERNAL_H
#define PARSE_INTERNAL_H

static inline const char *skip_spaces(const char *p)
{
    while (*p == ' ' || *p == '\t')
        p++;
    return p;
}

#endif
