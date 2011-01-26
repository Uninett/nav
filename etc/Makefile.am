include $(top_srcdir)/common.mk

scripts_in = $(wildcard init.d/*.in)
scripts_out = $(scripts_in:%.in=%)

cron_in = $(wildcard cron.d/*.in)
cron_out = $(cron_in:%.in=%)

EDITFILES = logger.conf webfront/webfront.conf apache/apache.conf $(scripts_out) $(cron_out)
nobase_dist_sysconf_DATA = $(sort $(wildcard *.conf) logger.conf) \
    $(sort $(wildcard webfront/*.txt webfront/*.conf) webfront/webfront.conf \
           apache/apache.conf apache/subsystems/*.conf \
	   alertprofiles/* \
	   arnold/*.conf arnold/mailtemplates/* \
	   portadmin/*.conf \
	   toolbox/*.tool \
	   rrdviewer/*.conf \
	   $(cron_out) \
	   report/*.conf report/*.html \
	   geomap/*.html geomap/*.py \
	   )

init_SCRIPTS = $(scripts_out)
