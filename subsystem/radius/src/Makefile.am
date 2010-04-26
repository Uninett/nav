include $(top_srcdir)/common.mk

cheetah_TEMPLATES = AcctChartsTemplate.py AcctDetailTemplate.py AcctSearchTemplate.py \
LogDetailTemplate.py LogTemplate.py
templatedir = $(pythondir)/nav/web/templates
template_PYTHON = $(cheetah_TEMPLATES)

radiuswebdir = $(webrootdir)/radius
radiusweb_PYTHON = radius.py radiuslib.py radius_config.py
radiusweb_DATA = .htaccess
bin_SCRIPTS = radiusparser.py

