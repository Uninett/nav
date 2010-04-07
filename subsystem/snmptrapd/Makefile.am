include $(top_srcdir)/common.mk

nobase_python_PYTHON = $(wildcard nav/snmptrapd/*.py nav/snmptrapd/handlers/*.py)
bin_SCRIPTS = snmptrapd.py
sysconf_DATA = snmptrapd.conf
init_SCRIPTS = snmptrapd
EDITFILES = $(init_SCRIPTS)
