nobase_python_PYTHON = $(wildcard nav/django/urls/*.py nav/web/networkexplorer/*.py)
tool_DATA = networkexplorer.tool

mytmpldir = $(djangotmpldir)/networkexplorer
mytmpl_DATA = $(wildcard templates/networkexplorer/*)

mywebdir = $(webrootdir)/networkexplorer
myweb_DATA = .htaccess
CLEANFILES = .htaccess

myimagedir = $(imagedir)/networkexplorer
myimage_DATA = $(wildcard media/images/networkexplorer/*)

stylesheet_DATA = $(wildcard media/style/*)
javascript_DATA = $(wildcard media/js/*)

.htaccess: htaccess
	cp htaccess .htaccess
