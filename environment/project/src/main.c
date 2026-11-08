#include <stdio.h>
#include <string.h>
#include "record.h"
#include "stats.h"
#include "version.h"

int main(int argc, char **argv)
{
    char buf[512];
    struct stats s;
    struct record r;
    int n = 0;

    if (argc > 1 && strcmp(argv[1], "--version") == 0) {
        printf("logstat %s\n", LOGSTAT_VERSION);
        return 0;
    }
    stats_init(&s);
    while (fgets(buf, sizeof buf, stdin)) {
        n++;
        if (parse_line(buf, n, &r) != 0)
            continue;
        stats_add(&s, &r);
#ifdef DEBUG
        fprintf(stderr, "debug: line %d level %d msg '%s'\n", r.line_no, r.level, r.msg);
#endif
    }
    report_print(&s);
    return 0;
}
