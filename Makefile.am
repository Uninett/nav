if INSTALL_CONF
    CONF_DIR = etc
endif

SUBDIRS = $(CONF_DIR) sql templates python bin doc htdocs

EXTRA_DIST = version.m4

install-data-local: installdirs

installdirs-local:
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log/arnold
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/run
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/rrd
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/rrd/activeip
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/uploads
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/uploads/images
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/uploads/images/rooms
