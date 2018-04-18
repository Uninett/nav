if INSTALL_CONF
    CONF_DIR = etc
endif
if BUILD_DOCS
    DOC_DIR = doc
endif

SUBDIRS = $(CONF_DIR) sql templates python bin $(DOC_DIR) htdocs

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
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/uploads/images/locations

pyclean:
	make -C bin pyclean
if BUILD_DOCS
	make -C doc pyclean
endif
	make -C python pyclean
