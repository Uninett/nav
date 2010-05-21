include $(top_srcdir)/common.mk

mywebdir = $(webrootdir)/l2trace
cheetah_TEMPLATES = nav/web/templates/l2traceTemplate.py
nobase_python_PYTHON = nav/web/l2trace.py $(cheetah_TEMPLATES)
myweb_DATA = .htaccess
tool_DATA = l2trace.tool
sysconf_DATA = l2trace.conf

