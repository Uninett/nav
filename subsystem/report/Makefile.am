include $(top_srcdir)/common.mk

templatesrc = $(wildcard nav/web/templates/*.tmpl)
cheetah_TEMPLATES = $(templatesrc:%.tmpl=%.py)
nobase_python_PYTHON = $(wildcard nav/*.py nav/report/*.py nav/web/report/*.py) $(cheetah_TEMPLATES)

reportconfdir = $(sysconfdir)/report
reportconf_DATA = $(wildcard etc/*.conf) etc/front.html

javascript_DATA = $(wildcard media/js/*)
stylesheet_DATA = $(wildcard media/style/*)
tool_DATA = report.tool

reportwebdir = $(webroot)/report
reportweb_DATA = .htaccess
CLEANFILES += .htaccess

.htaccess: htaccess
	cp htaccess .htaccess

