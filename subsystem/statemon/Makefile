#!/usr/bin/env make
# 
# This file is part of the NAV project and sånt
# 

# paths
PREFIX=/usr/local/nav
NAVVER=navme
PYLIB=$(PREFIX)/$(NAVVER)/lib/python/nav/statemon
BINDIR=$(PREFIX)/$(NAVVER)/bin
INITDIR=$(PREFIX)/$(NAVVER)/etc/init.d
INITFILES=pping servicemon
BINS=checkService.py pinger.py servicemon.py
LIBS=
CHECKERDIR=$(PYLIB)/checker
# programs to use for make
INSTALL=install

# ok, the targets
all: 
lib:
bin:
checker:

# the install
install: install-lib install-bin install-checker

install-lib: lib
	mkdir --parents $(PYLIB)
	for file in nav/statemon/*.py; do $(INSTALL) -m 644 $$file $(PYLIB)/; done
	mkdir --parents $(PYLIB)/DNS
	for file in nav/statemon/DNS/*.py; do $(INSTALL) -m 644 $$file $(PYLIB)/DNS/; done
install-bin: bin
	mkdir --parents $(BINDIR)
	for file in $(BINS);do $(INSTALL) -m 755 $$file $(BINDIR)/ ;done
	mkdir --parents $(INITDIR)
	for file in $(BINS); do $(INSTALL) -m 755 $$file $(INITDIR); done
install-checker: checker
	mkdir --parents $(CHECKERDIR)
	for file in nav/statemon/checker/*.py; do $(INSTALL) -m 644 $$file $(CHECKERDIR)/; done
	for file in nav/statemon/checker/*.descr; do $(INSTALL) -m 644 $$file $(CHECKERDIR)/; done
uninstall:
	for file in $(BINS); do rm -f $(BINDIR)/$$file; done	
	rm -rf $(CHECKERDIR)
	rm -rf $(PYLIB)
clean:
	find -name *.pyc -print0 | xargs --null rm -f