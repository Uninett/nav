include $(top_srcdir)/common.mk
SUBDIRS = media

bin_SCRIPTS = bin/navTemplate.py

webconfdir = $(sysconfdir)/webfront
webconf_DATA = $(wildcard config/webfront/*.txt config/webfront/*.conf) config/webfront/webfront.conf
EDITFILES = config/webfront/webfront.conf

templates_src = $(wildcard nav/web/templates/*.tmpl)
cheetah_TEMPLATES = $(templates_src:%.tmpl=%.py)
nobase_python_PYTHON = $(wildcard nav/web/*.py nav/django/urls/*.py nav/web/webfront/*.py) \
                       nav/web/templates/__init__.py \
		       $(cheetah_TEMPLATES)

mydjangotmpldir = $(djangotmpldir)/webfront
mydjangotmpl_DATA = $(wildcard templates/webfront/*)

webroot_DATA = .htaccess
CLEANFILES += .htaccess


.htaccess: htaccess
	cp htaccess .htaccess
