# logstat: summarise log levels from stdin.
# Builds bin/logstat (release) and bin/logstat-debug (prints each parsed record to stderr).
# Single non-recursive Makefile: every object lives under build/<variant>/, header
# dependencies come from the compiler (-MMD -MP), and gen/version.h is a real file target.

CC      = gcc
CFLAGS  = -O2 -Wall -Iinclude -Igen -Ilib
DEPFLAGS = -MMD -MP

BUILD   = build

LIB_SRCS = lib/parse.c lib/stats.c
APP_SRCS = src/main.c src/report.c

LIB_OBJS = $(patsubst lib/%.c,$(BUILD)/lib/%.o,$(LIB_SRCS))
REL_OBJS = $(patsubst src/%.c,$(BUILD)/release/%.o,$(APP_SRCS))
DBG_OBJS = $(patsubst src/%.c,$(BUILD)/debug/%.o,$(APP_SRCS))
LIBCORE  = $(BUILD)/libcore.a

.PHONY: all clean
.DELETE_ON_ERROR:

all: bin/logstat bin/logstat-debug

# Regenerated only when VERSION (or the generator) changes; written atomically so a
# parallel compile never sees a half-written header.
gen/version.h: VERSION scripts/genversion.sh
	@mkdir -p $(@D)
	sh scripts/genversion.sh VERSION > $@.tmp
	mv -f $@.tmp $@

$(BUILD)/lib/%.o: lib/%.c
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) $(DEPFLAGS) -c $< -o $@

# Order-only: the header must exist before the first compile; after that the .d files
# record exactly which objects really include it.
$(BUILD)/release/%.o: src/%.c | gen/version.h
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) $(DEPFLAGS) -c $< -o $@

$(BUILD)/debug/%.o: src/%.c | gen/version.h
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) -DDEBUG $(DEPFLAGS) -c $< -o $@

$(LIBCORE): $(LIB_OBJS)
	@mkdir -p $(@D)
	rm -f $@
	ar rcs $@ $^

bin/logstat: $(REL_OBJS) $(LIBCORE)
	@mkdir -p $(@D)
	$(CC) -o $@ $^

bin/logstat-debug: $(DBG_OBJS) $(LIBCORE)
	@mkdir -p $(@D)
	$(CC) -o $@ $^

clean:
	rm -rf $(BUILD) bin gen
	rm -f src/*.o lib/*.o lib/libcore.a

-include $(LIB_OBJS:.o=.d) $(REL_OBJS:.o=.d) $(DBG_OBJS:.o=.d)
