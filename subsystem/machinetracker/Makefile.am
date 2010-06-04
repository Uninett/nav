mywebdir = ${webroot}/machinetracker
mytemplatedir = $(djangotmpldir)/machinetracker

nobase_python_PYTHON = $(wildcard nav/django/urls/*.py nav/web/*/*.py)
tool_DATA = machinetracker.tool
mytemplate_DATA = $(wildcard templates/machinetracker/*)
stylesheet_DATA = $(wildcard media/style/*)
myweb_DATA = .htaccess
CLEANFILES = .htaccess

.htaccess: htaccess
	cp htaccess .htaccess
