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
	docker run -t -u $(uid):$(gid) -v $(top_srcdir):/source $(name) /source/tests/docker/test.sh

lint: build
	docker run -t -u $(uid):$(gid) -v $(top_srcdir):/source $(name) /pylint.sh

shell:
	docker run -t --rm -u $(uid):$(gid) -v $(top_srcdir):/source $(name) /bin/bash

name:
	echo Image name: $(name)

clean:
	rm -f runtime-requirements.txt test-requirements.txt
	find . -name '*.pyc' -exec rm -rf '{}' +
	find . -name __pycache__ -exec rmdir '{}' +
