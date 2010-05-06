include $(top_srcdir)/common.mk

init_SCRIPTS = ipdevpoll
EDITFILES = $(init_SCRIPTS)

bin_SCRIPTS = ipdevpolld
nobase_python_PYTHON = $(wildcard nav/ipdevpoll/*.py nav/ipdevpoll/*/*.py nav/mibs/*.py nav/*.py)
sysconf_DATA = ipdevpoll.conf

