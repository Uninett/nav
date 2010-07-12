mywebdir = ${webroot}/seeddb
mytemplatedir = $(djangotmpldir)/seeddb

nobase_python_PYTHON = $(wildcard nav/django/urls/*.py nav/web/*/*.py)
tool_DATA = seeddb.tool
mytemplate_DATA = $(wildcard templates/seeddb/*)
javascript_DATA = $(wildcard media/js/*)
myweb_DATA = .htaccess
CLEANFILES = .htaccess

.htaccess: htaccess
	cp htaccess .htaccess
