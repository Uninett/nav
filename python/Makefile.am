include $(top_srcdir)/common.mk

pathmodule = nav/buildconf.py
EDITFILES = $(pathmodule)

templates_src = $(wildcard nav/web/templates/*.tmpl)
cheetah_TEMPLATES = $(templates_src:%.tmpl=%.py)

nobase_python_DATA = $(sort $(wildcard nav/*.py) \
                            $(wildcard nav/*/*.py) \
                            $(wildcard nav/*/*/*.py) \
                            $(wildcard nav/*/*/*/*.py) \
                            $(pathmodule) \
                            $(cheetah_TEMPLATES) \
                            $(wildcard nav/statemon/checker/*.descr) \
                            )

all: $(cheetah_TEMPLATES) $(pathmodule)

check: all
	PYTHONPATH=. ./runtests.py $(top_srcdir)/tests/unittests
	@echo
	@echo "*** Remember to also run the integration ***"
	@echo "*** tests on a fully installed system    ***"
	@echo
