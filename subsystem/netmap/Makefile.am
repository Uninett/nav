include $(top_srcdir)/common.mk


cheetah_src = $(wildcard nav/web/templates/*.tmpl)
cheetah_TEMPLATES = $(cheetah_src:%.tmpl=%.py)

nobase_python_PYTHON = $(wildcard nav/web/netmap/*.py) $(cheetah_TEMPLATES)

mywebdir = $(webrootdir)/netmap
myweb_DATA = .htaccess
CLEANFILES += .htaccess

.htaccess: htaccess
	cp htaccess .htaccess
