nobase_python_PYTHON = $(wildcard nav/*.py nav/web/*/*.py nav/django/urls/*.py)
tool_DATA = useradmin.tool

mytmpldir = $(djangotmpldir)/useradmin
mytmpl_DATA = $(wildcard templates/useradmin/*)

adminwebdir = $(webrootdir)/useradmin
infowebdir = $(webrootdir)/userinfo
adminweb_DATA = .htaccess
infoweb_DATA = .htaccess
CLEANFILES = .htaccess

.htaccess: htaccess Makefile
	cp htaccess .htaccess

