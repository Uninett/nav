include $(top_srcdir)/common.mk

scripts_in = $(wildcard init.d/*.in)
scripts_out = $(scripts_in:%.in=%)

cron_in = $(wildcard cron.d/*.in)
cron_out = $(cron_in:%.in=%)

generated_config = logger.conf pping.conf servicemon.conf webfront/webfront.conf apache/apache.conf $(cron_out)

EDITFILES = $(generated_config) $(scripts_out)
nobase_dist_sysconf_DATA = $(sort $(generated_config) $(wildcard \
	*.conf \
	webfront/*.txt \
	webfront/*.conf \
	apache/apache.conf \
	apache/subsystems/*.conf \
	alertprofiles/* \
	arnold/*.conf \
	arnold/mailtemplates/* \
	portadmin/*.conf \
	toolbox/*.tool \
	rrdviewer/*.conf \
	report/*.conf \
	report/*.html \
	geomap/*.html \
	geomap/*.py \
	))

init_SCRIPTS = $(scripts_out)
