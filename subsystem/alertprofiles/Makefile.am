WEBNAME = alertprofiles

mywebdir = ${webroot}/alertprofiles
myconfdir = $(sysconfdir)/alertprofiles
mytemplatedir = $(djangotmpldir)/alertprofiles
myimagedir = $(imagedir)/alertprofiles

nobase_python_PYTHON = $(wildcard nav/django/urls/alertprofiles.py nav/web/alertprofiles/*.py)
myconf_DATA = $(wildcard config/alertprofiles/*)
tool_DATA = alertprofiles.tool
mytemplate_DATA = $(wildcard templates/alertprofiles/*)
myimage_DATA = $(wildcard images/alertprofiles/*)
stylesheet_DATA = $(wildcard media/style/*)
javascript_DATA = $(wildcard media/js/*)
myweb_DATA = .htaccess
CLEANFILES = .htaccess

.htaccess: htaccess
	cp htaccess .htaccess
