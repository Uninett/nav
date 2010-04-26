# Names
subsystem = devicehistory
mywebdir = $(webrootdir)/$(subsystem)
mytemplatedir = $(djangotmpldir)/$(subsystem)

nobase_python_PYTHON = $(wildcard nav/django/urls/*.py nav/web/*/*.py nav/web/*/*/*.py)
tool_DATA = devicehistory.tool
javascript_DATA = $(wildcard media/js/*)
stylesheet_DATA = $(wildcard media/style/*)
mytemplate_DATA = $(wildcard templates/$(subsystem)/*)
myweb_DATA = .htaccess

CLEANFILES = .htaccess

.htaccess: htaccess
	cp htaccess .htaccess
