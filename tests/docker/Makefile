mkfile_dir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
top_srcdir := $(mkfile_dir)../..
name := navtest:$(shell git describe --tags)
uname := $(shell uname)
uid := $(shell id -u)
gid := $(shell id -g)

.PHONY: build check

build:
	docker build -t $(name) -f Dockerfile $(top_srcdir)

buildnocache:
	docker build --no-cache -t $(name) -f Dockerfile $(top_srcdir)

check: build
	/usr/bin/env
	docker run -u $(uid):$(gid) -v $(top_srcdir):/source $(name) /source/tests/docker/test.sh

lint: build
	/usr/bin/env
	docker run -u $(uid):$(gid) -v $(top_srcdir):/source $(name) /pylint.sh

shell:
	docker run -ti --rm -u $(uid):$(gid) -v $(top_srcdir):/source $(name) /bin/bash

name:
	echo Image name: $(name)

clean:
	rm -f runtime-requirements.txt test-requirements.txt
