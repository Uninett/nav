SUBDIRS = src \
	subsystem/alertengine \
	subsystem/alertprofiles \
	subsystem/arnold \
	subsystem/dbTools \
	subsystem/devicehistory \
	subsystem/ipdevinfo \
	subsystem/ipinfo \
	subsystem/l2trace \
	subsystem/lib-perl \
	subsystem/lib-python \
	subsystem/logger \
	subsystem/machinetracker \
	subsystem/mailin \
	subsystem/maintenance \
	subsystem/messages \
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
	subsystem/useradmin \
	subsystem/webfront

sysconf_DATA = doc/conf/db.conf doc/conf/nav.conf 

EXTRA_DIST = version.m4

install-data-hook: webfix

#installdirs:
#	$(INSTALL) -v -m 0755 -d $(DESTDIR)$(prefix)
#	$(INSTALL) -v -m 0755 -d $(DESTDIR)$(exec_prefix)
#	$(INSTALL) -v -m 0775 -d $(DESTDIR)$(sysconfdir)
#	$(INSTALL) -v -m 0775 -d $(DESTDIR)$(crondir)
#	$(INSTALL) -v -m 0755 -d $(DESTDIR)$(bindir)
#	$(INSTALL) -v -m 0755 -d $(DESTDIR)$(docdir)
#	$(INSTALL) -v -m 0755 -d $(DESTDIR)$(libdir)
#	$(INSTALL) -v -m 0755 -d $(DESTDIR)$(javalibdir)
#	$(INSTALL) -v -m 0755 -d $(DESTDIR)$(perllibdir)
#	$(INSTALL) -v -m 0755 -d $(DESTDIR)$(pythonlibdir)
#	$(INSTALL) -v -m 0755 -d $(DESTDIR)$(webapps)
#	$(INSTALL) -v -m 0755 -d $(DESTDIR)$(webroot)
#	$(INSTALL) -v -m 0775 -d $(DESTDIR)$(tooldir)
#	$(INSTALL) -v -m 2775 -d $(DESTDIR)$(localstatedir)
#	$(INSTALL) -v -m 2775 -d $(DESTDIR)$(localstatedir)/log
#	$(INSTALL) -v -m 2775 -d $(DESTDIR)$(localstatedir)/log/arnold
#	$(INSTALL) -v -m 2775 -d $(DESTDIR)$(localstatedir)/log/eventEngine
#	$(INSTALL) -v -m 2775 -d $(DESTDIR)$(localstatedir)/log/getDeviceData
#	$(INSTALL) -v -m 2775 -d $(DESTDIR)$(localstatedir)/log/networkDiscovery
#	$(INSTALL) -v -m 2775 -d $(DESTDIR)$(localstatedir)/run
#	$(INSTALL) -v -m 2775 -d $(DESTDIR)$(localstatedir)/rrd

webfix:
	tools/htpython.sh $(DESTDIR)$(webroot) $(webroot)

