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

clean-local:
	find . -name __pycache__ -exec rm -rf '{}' +
	find . -name '*.pyc' -exec rm -f '{}' +
