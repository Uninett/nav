mkfile_dir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
top_srcdir := $(mkfile_dir)../..
uname := $(shell uname)
dockerfile := Dockerfile

name := navtest:$(shell git describe --tags)-$(dockerfile)

.PHONY: build check

build:
	docker build -t $(name) -f $(dockerfile) $(mkfile_dir)

buildnocache:
	docker build --no-cache -t $(name) -f $(dockerfile) $(mkfile_dir)

check: build
	docker run -t -v $(top_srcdir):/source --tmpfs /var/lib/postgresql $(name) /source/tests/docker/test.sh

# Runs an ephemeral container with core dumping capabilities and PostgreSQL on an in-memory tmpfs
shell:
	docker run -ti --rm --ulimit core=-1 -v $(top_srcdir):/source --tmpfs /var/lib/postgresql $(name) /bin/bash

name:
	echo Image name: $(name)

clean:
	find . -name '*.pyc' -exec rm -rf '{}' +
	find . -name __pycache__ -exec rmdir '{}' +
