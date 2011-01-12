include $(top_srcdir)/common.mk

pathmodule = nav/buildconf.py
EDITFILES = $(pathmodule)

templates_src = $(wildcard nav/web/templates/*.tmpl)
cheetah_TEMPLATES = $(templates_src:%.tmpl=%.py)

nobase_python_PYTHON = $(sort $(wildcard nav/*.py) \
                              $(wildcard nav/*/*.py) \
			      $(wildcard nav/*/*/*.py) \
			      $(wildcard nav/*/*/*/*.py) \
			      $(pathmodule) \
			      $(cheetah_TEMPLATES) \
			      )

nobase_python_DATA = $(wildcard nav/statemon/checker/*.descr)
