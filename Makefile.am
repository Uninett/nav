SUBDIRS = src \
	doc \
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

install-data-local: installdirs

installdirs-local:
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/log
	$(INSTALL) -m 2775 -d $(DESTDIR)$(localstatedir)/run

webfix:
	tools/htpython.sh $(DESTDIR)$(webroot) $(webroot)

