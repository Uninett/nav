#!/usr/bin/env make
# 
# This file is part of the NAV project and sånt
# 

# paths
PREFIX=/usr/local/nav
NAVVER=navme
PYLIB=$(PREFIX)/$(NAVVER)/lib/python
WEBLIB=$(PYLIB)/nav/web
WEBROOT=$(PREFIX)/$(NAVVER)/apache/webroot
WEBNAME=browse
WEBDIR=$(WEBROOT)/$(WEBNAME)
WEBLIBS=indexer.py netbox.py room.py service.py
LIBS=urlbuilder.py
# programs to use for make
INSTALL=install

# ok, the targets
all: 
lib:
web:

# the install
install: install-lib install-web

install-lib: lib
	mkdir --parents $(WEBLIB)/devBrowser
	touch $(WEBLIB)/index.py
	touch $(WEBLIB)/devBrowser/index.py
	for file in $(LIBS); do $(INSTALL) -m 644 lib/$$file $(WEBLIB)/devBrowser/; done
	$(INSTALL) -m 644 lib/urlbuilder.py $(WEBLIB)    
	
install-web: web
	mkdir --parents $(WEBDIR)
	$(INSTALL) -m 644 htaccess $(WEBDIR)/.htaccess

uninstall:
	for file in $(LIBS); do rm -f $(WEBLIB)/devBrowser/$$file; done	
	rm -f $(WEBLIB)/devBrowser/index.py
	rm -f $(WEBLIB)/urlbuilder
	rmdir --parents --ignore-fail-on-non-empty $(WEBLIB)/devBrowser

clean:
	find -name *.pyc -print0 | xargs --null rm -f
    
