include $(top_srcdir)/common.mk

SUBDIRS = templates

pathmodule = nav/buildconf.py
EDITFILES = $(pathmodule)
nobase_python_DATA = $(sort $(wildcard nav/*.py) $(wildcard nav/*/*.py) $(wildcard nav/*/*/*.py) $(pathmodule))
bin_SCRIPTS = bin/hasPrivilege.py

