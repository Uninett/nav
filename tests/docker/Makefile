mkfile_dir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
top_srcdir := $(mkfile_dir)../..
name := navtest:$(shell git describe --tags)
uname := $(shell uname)
ifeq ($(uname), Darwin)
 runas := build
else
 runas := root
endif

.PHONY: build check

build: runtime-requirements.txt test-requirements.txt
	docker build -t $(name) $(mkfile_dir)

buildnocache: runtime-requirements.txt test-requirements.txt
	docker build --no-cache -t $(name) $(mkfile_dir)

check: build
# Running in privileged mode because Google Chrome apparently requires it
	/usr/bin/env
	docker run -u $(runas) --privileged -v $(top_srcdir):/source $(name) /source/tests/docker/test.sh

lint: build
	/usr/bin/env
	docker run -u $(runas) -v $(top_srcdir):/source $(name) /source/tests/docker/lint.sh

shell:
	docker run -u $(runas) -t -i --privileged -v $(top_srcdir):/source $(name) /bin/bash

runtime-requirements.txt: $(top_srcdir)/requirements/*
	cat $^ > $@

test-requirements.txt: $(top_srcdir)/tests/requirements.txt
	cp -a $< $@

name:
	echo Image name: $(name)

clean:
	rm -f runtime-requirements.txt test-requirements.txt
	find . -name '*.pyc' -exec rm -rf '{}' +
	find . -name __pycache__ -exec rmdir '{}' +
