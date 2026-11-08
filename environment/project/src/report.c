#include <stdio.h>
#include "stats.h"

void report_print(const struct stats *s)
{
    printf("INFO %ld\n", s->count[LVL_INFO]);
    printf("WARN %ld\n", s->count[LVL_WARN]);
    printf("ERROR %ld\n", s->count[LVL_ERROR]);
    printf("UNKNOWN %ld\n", s->count[LVL_UNKNOWN]);
    printf("total %ld\n", s->total);
}
