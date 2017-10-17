mkfile_dir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
top_srcdir := $(mkfile_dir)../..
uname := $(shell uname)
uid := $(shell id -u)
gid := $(shell id -g)

ifeq ($(PYTHON_VERSION),3)
  dockerfile := Dockerfile3
else
  dockerfile := Dockerfile
endif

name := navtest:$(shell git describe --tags)-$(dockerfile)

.PHONY: build check

build:
	docker build -t $(name) -f $(dockerfile) $(top_srcdir)

buildnocache:
	docker build --no-cache -t $(name) -f $(dockerfile) $(top_srcdir)

check: build
	docker run -t -u $(uid):$(gid) -v $(top_srcdir):/source $(name) /source/tests/docker/test.sh

lint: build
	docker run -t -u $(uid):$(gid) -v $(top_srcdir):/source $(name) /pylint.sh

shell:
	docker run -ti --rm -u $(uid):$(gid) -v $(top_srcdir):/source $(name) /bin/bash

name:
	echo Image name: $(name)

clean:
	rm -f runtime-requirements.txt test-requirements.txt
	find . -name '*.pyc' -exec rm -rf '{}' +
	find . -name __pycache__ -exec rmdir '{}' +
