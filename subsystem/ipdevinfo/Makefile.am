SUBDIRS = config templates

ipdevinfowebdir = $(webrootdir)/ipdevinfo
rrdviewerwebdir = $(webrootdir)/rrdviewer
nobase_python_PYTHON = $(wildcard nav/django/urls/*.py nav/web/*/*.py)

tool_DATA = ipdevinfo.tool
ipdevinfoweb_DATA = .htaccess
rrdviewerweb_DATA = .htaccess
stylesheet_DATA = $(wildcard media/style/*)

CLEANFILES = .htaccess

.htaccess: htaccess
	cp htaccess .htaccess
