SUBDIRS = java \
	doc \
	etc \
	sql \
	templates \
	python \
	bin \
	media \
	subsystem/ipdevpoll \
	subsystem/radius

EXTRA_DIST = version.m4

install-data-hook: webfix

install-data-local: installdirs

installdirs-local:
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log/arnold
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/run
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/rrd


webfix:
	tools/htpython.sh $(DESTDIR)$(webroot) $(webroot)

