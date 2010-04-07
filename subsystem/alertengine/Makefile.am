include $(top_srcdir)/common.mk

bin_SCRIPTS = alertengine.py
nobase_python_PYTHON = $(wildcard nav/alertengine/*.py nav/alertengine/*/*.py)
sysconf_DATA = alertengine.conf 
nobase_sysconf_DATA = init.d/alertengine
EDITFILES = $(nobase_sysconf_DATA)
