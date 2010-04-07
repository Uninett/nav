include $(top_srcdir)/common.mk

rrddir = $(localstatedir)/rrd
init_SCRIPTS = pping servicemon
bin_SCRIPTS = checkService.py pping.py servicemon.py
sysconf_DATA = servicemon.conf pping.conf
EDITFILES = $(sysconf_DATA)

nobase_python_PYTHON = $(wildcard nav/statemon/*.py nav/statemon/DNS/*.py nav/statemon/checker/*.py)
nobase_python_DATA = $(wildcard nav/statemon/checker/*.descr)

install-data-local: installdirs

# Create the RRD data directory needed by statemon
installdirs-local:
	$(INSTALL) -m 775 -d $(DESTDIR)$(rrddir)
