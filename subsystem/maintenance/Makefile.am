include $(top_srcdir)/common.mk

mywebdir = $(webrootdir)/maintenance
bin_SCRIPTS = $(wildcard bin/*.py)

cron_DATA = cron.d/maintengine
tool_DATA = maintenance.tool

templates_src = $(wildcard nav/web/templates/*.tmpl)
cheetah_TEMPLATES = $(templates_src:%.tmpl=%.py)

nobase_python_PYTHON = $(wildcard nav/*.py nav/web/maintenance/*.py) $(cheetah_TEMPLATES)

myweb_DATA = .htaccess
CLEANFILES += .htaccess

.htaccess: htaccess
	cp htaccess .htaccess

