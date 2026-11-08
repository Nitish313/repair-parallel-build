CC = gcc
CFLAGS = -O2 -Wall -I../include -I.

OBJS = parse.o stats.o

libcore.a: $(OBJS)
	ar rcs $@ $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: clean
clean:
	rm -f *.o libcore.a
