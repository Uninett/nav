include $(top_srcdir)/common.mk

bin_SCRIPTS = alertengine.py
nobase_python_PYTHON = $(wildcard nav/alertengine/*.py nav/alertengine/*/*.py)
sysconf_DATA = alertengine.conf 
init_SCRIPTS = init.d/alertengine
EDITFILES = $(init_SCRIPTS)
