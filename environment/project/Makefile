# logstat: summarise log levels from stdin.
# Builds bin/logstat (release) and bin/logstat-debug (prints each parsed record to stderr).

CC = gcc
CFLAGS = -O2 -Wall -Iinclude -Igen -Ilib

SRCS = src/main.c src/report.c
OBJS = $(SRCS:.c=.o)

.PHONY: all clean version

all: version bin/logstat bin/logstat-debug

version:
	mkdir -p gen
	sh scripts/genversion.sh VERSION > gen/version.h

lib/libcore.a:
	$(MAKE) -C lib

bin/logstat: $(OBJS) lib/libcore.a
	mkdir -p bin
	$(CC) -o $@ $(OBJS) lib/libcore.a

bin/logstat-debug: $(SRCS) lib/libcore.a
	mkdir -p bin
	$(CC) $(CFLAGS) -DDEBUG -c src/main.c -o src/main.o
	$(CC) $(CFLAGS) -DDEBUG -c src/report.c -o src/report.o
	$(CC) -o $@ $(OBJS) lib/libcore.a

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f src/*.o bin/logstat bin/logstat-debug gen/version.h
	$(MAKE) -C lib clean
