#include "stats.h"

void stats_init(struct stats *s)
{
    int i;
    for (i = 0; i < LVL_COUNT; i++)
        s->count[i] = 0;
    s->total = 0;
}

void stats_add(struct stats *s, const struct record *r)
{
    if (r->level >= 0 && r->level < LVL_COUNT)
        s->count[r->level]++;
    else
        s->count[LVL_UNKNOWN]++;
    s->total++;
}
