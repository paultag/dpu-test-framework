# Copyright (c) DPU AUTHORS, 2012, under the terms of GPL-2+, if it's at all
# copyrightable. Which I doubt.

CC=gcc
CFLAGS=-Wall -O0

all: clean build

.c.o:
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -fv hello

build: hello

install:
	mkdir -p $(DESTDIR)/usr/bin
	cp -v hello $(DESTDIR)/usr/bin
