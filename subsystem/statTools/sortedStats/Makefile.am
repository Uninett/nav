include $(top_srcdir)/common.mk

weblibdir = $(pythondir)/nav/web
templatedir = $(weblibdir)/templates

cheetah_TEMPLATES = SortedStatsTemplate.py
template_PYTHON = $(cheetah_TEMPLATES)

sysconf_DATA = sortedStats.conf
weblib_PYTHON = sortedStats.py

statswebdir = $(webrootdir)/stats
statsweb_DATA = .htaccess
CLEANFILES += .htaccess

.htaccess: htaccess
	cp htaccess .htaccess
