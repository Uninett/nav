include $(top_srcdir)/common.mk


cheetah_src = $(wildcard nav/web/templates/*.tmpl)
cheetah_TEMPLATES = $(cheetah_src:%.tmpl=%.py)

nobase_python_PYTHON = $(wildcard nav/*.py nav/web/messages/*.py) $(cheetah_TEMPLATES)
tool_DATA = messages.tool

mywebdir = $(webrootdir)/messages
myweb_DATA = .htaccess
CLEANFILES += .htaccess

.htaccess: htaccess
	cp htaccess .htaccess
