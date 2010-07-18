include $(top_srcdir)/common.mk

bin_SCRIPTS = bin/navTemplate.py

templates_src = $(wildcard nav/web/templates/*.tmpl)
cheetah_TEMPLATES = $(templates_src:%.tmpl=%.py)
nobase_python_PYTHON = $(wildcard nav/web/*.py nav/django/urls/*.py nav/web/webfront/*.py) \
                       nav/web/templates/__init__.py \
		       $(cheetah_TEMPLATES)

