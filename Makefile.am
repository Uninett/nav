SUBDIRS = java \
	doc \
	etc \
	sql \
	templates \
	python \
	bin \
	media \
	subsystem/ipdevpoll \
	subsystem/mailin \
	subsystem/netmap \
	subsystem/networkexplorer \
	subsystem/radius \
	subsystem/report \
	subsystem/seeddb \
	subsystem/smsd \
	subsystem/snmptrapd \
	subsystem/startstop \
	subsystem/statTools \
	subsystem/statemon \
	subsystem/status \
	subsystem/thresholdMon \
	subsystem/useradmin

EXTRA_DIST = version.m4

install-data-hook: webfix

install-data-local: installdirs

installdirs-local:
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log/arnold
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/run


webfix:
	tools/htpython.sh $(DESTDIR)$(webroot) $(webroot)

