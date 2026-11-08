#ifndef STATS_H
#define STATS_H

#include "record.h"

struct stats {
    long count[LVL_COUNT];
    long total;
};

void stats_init(struct stats *s);
void stats_add(struct stats *s, const struct record *r);
void report_print(const struct stats *s);

#endif
