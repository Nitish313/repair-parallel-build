#ifndef RECORD_H
#define RECORD_H

#define MSG_MAX 64

enum level { LVL_INFO, LVL_WARN, LVL_ERROR, LVL_UNKNOWN, LVL_COUNT };

struct record {
    int level;
    int line_no;
    char msg[MSG_MAX];
};

/* Parse one "LEVEL message" line. Returns 0 on success, -1 for a blank line. */
int parse_line(const char *line, int line_no, struct record *out);

#endif
