include $(top_srcdir)/common.mk

templates_src = $(wildcard nav/web/templates/*.tmpl)
cheetah_TEMPLATES = $(templates_src:%.tmpl=%.py)

nobase_python_PYTHON = $(wildcard nav/*.py nav/web/*/*.py nav/django/urls/*.py) $(cheetah_TEMPLATES)
tool_DATA = status.tool

statustmpldir = $(djangotmpldir)/status
statustmpl_DATA = $(wildcard templates/status/*)

statuswebdir = $(webrootdir)/status
statusweb_DATA = .htaccess
CLEANFILES += .htaccess

.htaccess: htaccess
	cp htaccess .htaccess


