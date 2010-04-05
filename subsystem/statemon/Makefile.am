rrddir = $(localstatedir)/rrd
init_SCRIPTS = pping servicemon
bin_SCRIPTS = checkService.py pping.py servicemon.py
sysconf_DATA = servicemon.conf pping.conf
CLEANFILES = $(sysconf_DATA)

nobase_python_PYTHON = $(wildcard nav/statemon/*.py nav/statemon/DNS/*.py nav/statemon/checker/*.py)
nobase_python_DATA = $(wildcard nav/statemon/checker/*.descr)

pping.conf: pping.conf.source Makefile
	$(top_srcdir)/tools/expand.pl pping.conf.source > pping.conf
	
servicemon.conf: servicemon.conf.source Makefile
	$(top_srcdir)/tools/expand.pl servicemon.conf.source > servicemon.conf

install-data-local: installdirs

# Create the RRD data directory needed by statemon
installdirs-local:
	$(INSTALL) -m 775 -d $(DESTDIR)$(rrddir)
