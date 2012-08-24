# Copyright (c) DPU AUTHORS, 2012, under the terms of GPL-2+, if it's at all
# copyrightable. Which I doubt.

all: build
build:
	echo "No-op"

install:
	mkdir -p $(DESTDIR)/usr/bin
	mkdir -p $(DESTDIR)/usr/share/man/man1
	cp -v hello $(DESTDIR)/usr/bin
	if [ -e hello.1.gz ]; then \
		cp hello.1.gz $(DESTDIR)/usr/share/man/man1; \
	fi
