mkfile_dir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
top_srcdir := $(mkfile_dir)../..
name := nav-$(shell hg parent --template '{node}')

.PHONY: build check

build: runtime-requirements.txt test-requirements.txt
	docker build -t $(name) $(mkfile_dir)

check: build
# Running in privileged mode because Google Chrome apparently requires it
	docker run --privileged -v $(top_srcdir):/source $(name)

ucheck: build
	docker run -v $(top_srcdir):/source $(name)

runtime-requirements.txt: $(top_srcdir)/requirements.txt
	cp $< $@

test-requirements.txt: $(top_srcdir)/tests/requirements.txt
	cp $< $@

name:
	echo Image name: $(name)
