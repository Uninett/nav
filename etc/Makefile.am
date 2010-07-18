include $(top_srcdir)/common.mk

SUBDIRS = init.d

EDITFILES = webfront/webfront.conf apache/apache.conf
nobase_dist_sysconf_DATA = $(wildcard *.conf) \
    $(sort $(wildcard webfront/*.txt webfront/*.conf) webfront/webfront.conf \
           apache/apache.conf apache/subsystems/*.conf \
	   alertprofiles/* \
	   arnold/*.conf arnold/mailtemplates/* \
	   toolbox/*.tool \
	   )

