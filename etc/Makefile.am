include $(top_srcdir)/common.mk

scripts_in = $(wildcard init.d/*.in)
scripts_out = $(scripts_in:%.in=%)

EDITFILES = webfront/webfront.conf apache/apache.conf $(scripts_out)
nobase_dist_sysconf_DATA = $(wildcard *.conf) \
    $(sort $(wildcard webfront/*.txt webfront/*.conf) webfront/webfront.conf \
           apache/apache.conf apache/subsystems/*.conf \
	   alertprofiles/* \
	   arnold/*.conf arnold/mailtemplates/* \
	   toolbox/*.tool \
	   )

init_SCRIPTS = $(scripts_out)
