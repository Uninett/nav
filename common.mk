# Common NAV make file rules
CLEANFILES = $(cheetah_TEMPLATES)

$(cheetah_TEMPLATES): %.py: %.tmpl
	$(CHEETAH) compile $<

all: $(cheetah_TEMPLATES)
