include $(top_srcdir)/common.mk

pathmodule = nav/buildconf.py
EDITFILES = $(pathmodule)

nobase_python_DATA = $(sort $(wildcard nav/*.py) \
                            $(wildcard nav/*/*.py) \
                            $(wildcard nav/*/*/*.py) \
                            $(wildcard nav/*/*/*/*.py) \
                            $(wildcard nav/*/*/*/*/*.py) \
                            $(pathmodule) \
                            )

all: $(pathmodule)

check: all
	PYTHONPATH=. ./runtests.py $(top_srcdir)/tests/unittests
	@echo
	@echo "*** Remember to also run the integration ***"
	@echo "*** tests on a fully installed system    ***"
	@echo
