SUBDIRS = java \
	etc \
	sql \
	templates \
	python \
	bin \
	doc \
	media

EXTRA_DIST = version.m4

install-data-local: installdirs

installdirs-local:
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log/arnold
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/run
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/rrd


