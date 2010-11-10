include $(top_srcdir)/common.mk
SUBDIRS = media

templates_src = $(wildcard nav/web/templates/*.tmpl)
cheetah_TEMPLATES = $(templates_src:%.tmpl=%.py)

mytemplatedir = $(djangotmpldir)/geomap
mytemplate_DATA = $(wildcard templates/geomap/*)

geomapconfdir = $(sysconfdir)/geomap
geomapconf_DATA = $(wildcard config/geomap/*.html config/geomap/*.py)

tool_DATA = geomap.tool

nobase_python_PYTHON = $(wildcard nav/django/urls/geomap.py nav/web/geomap/*.py) $(cheetah_TEMPLATES)

geomapwebdir = $(webroot)/geomap
geomapweb_DATA = .htaccess
CLEANFILES += .htaccess

.htaccess: htaccess
	cp htaccess .htaccess
