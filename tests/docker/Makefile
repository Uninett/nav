mkfile_dir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
top_srcdir := $(mkfile_dir)../..

.PHONY: build check

build: runtime-requirements.txt test-requirements.txt
	docker build -t testus $(mkfile_dir)

check:
	docker run --privileged -v $(top_srcdir):/source testus

runtime-requirements.txt: $(top_srcdir)/requirements.txt
	cp $< $@

test-requirements.txt: $(top_srcdir)/tests/requirements.txt
	cp $< $@
