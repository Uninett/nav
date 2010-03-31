include $(top_srcdir)/common.mk

SUBDIRS = config
mywebdir = $(webrootdir)/arnold
myimagedir = $(imagedir)/arnold

cheetah_TEMPLATES = nav/web/templates/ArnoldTemplate.py
nobase_python_PYTHON = nav/arnold.py nav/web/arnoldhandler.py $(cheetah_TEMPLATES)
myweb_DATA = .htaccess
bin_SCRIPTS = arnold.py autoenable.py start_arnold.py t1000.py
myimage_DATA = images/details.png  images/enable.png
tool_DATA = arnold.tool


