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
WEBLIBS=netbox.py module.py port.py service.py servicetable.py dispatcher.py rrd.py
# programs to use for make
INSTALL=install

# ok, the targets
all: 
lib:
web:

# the install
install: install-lib install-web

install-lib: lib
	$(INSTALL) -d $(WEBLIB)/devBrowser
	touch $(WEBLIB)/__init__.py
	touch $(WEBLIB)/devBrowser/__init__.py
	for file in $(WEBLIBS); do $(INSTALL) -m 644 lib/$$file $(WEBLIB)/devBrowser/; done
	
install-web: web
	$(INSTALL) -d $(WEBDIR)
	$(INSTALL) -m 644 htaccess $(WEBDIR)/.htaccess
	# Apache is lame and needs an EXISTING FILE to use 
	# DirectoryIndex...... so let's create an empty one
	touch $(WEBDIR)/index

uninstall: uninstall-web uninstall-lib
uninstall-lib:
	-for file in $(WEBLIBS); do rm -f $(WEBLIB)/devBrowser/$$file; done	
	-rm -f $(WEBLIB)/devBrowser/__init__.py
	-rmdir --parents $(WEBLIB)/devBrowser
uninstall-web:
	-rm -f $(WEBDIR)/.htaccess
	-rmdir --parents $(WEBDIR)

clean:
	find -name *.pyc -print0 | xargs --null rm -f
	
