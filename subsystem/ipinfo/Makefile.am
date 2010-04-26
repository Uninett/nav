include $(top_srcdir)/common.mk

mywebdir = $(webrootdir)/ipinfo
cheetah_TEMPLATES = nav/web/templates/IPInfo.py
nobase_python_PYTHON = $(wildcard nav/web/ipinfo/*) $(cheetah_TEMPLATES)

webconfdir = $(sysconfdir)/webfront
webconf_DATA = ipinfo.conf
myweb_DATA = .htaccess

