# Common NAV make file rules
edit = $(SED) \
        -e 's|@VERSION[@]|$(VERSION)|g' \
        -e 's|@bindir[@]|$(bindir)|g' \
        -e 's|@crondir[@]|$(crondir)|g' \
        -e 's|@djangotmpldir[@]|$(djangotmpldir)|g' \
        -e 's|@docdir[@]|$(docdir)|g' \
        -e 's|@exec_prefix[@]|$(exec_prefix)|g' \
        -e 's|@imagedir[@]|$(imagedir)|g' \
        -e 's|@initdir[@]|$(initdir)|g' \
        -e 's|@javalibdir[@]|$(javalibdir)|g' \
        -e 's|@javascriptdir[@]|$(javascriptdir)|g' \
        -e 's|@libdir[@]|$(libdir)|g' \
        -e 's|@localstatedir[@]|$(localstatedir)|g' \
        -e 's|@nav_user[@]|$(nav_user)|g' \
        -e 's|@perllibdir[@]|$(perllibdir)|g' \
        -e 's|@prefix[@]|$(prefix)|g' \
        -e 's|@pythondir[@]|$(pythondir)|g' \
        -e 's|@pythonlibdir[@]|$(pythonlibdir)|g' \
        -e 's|@stylesheetdir[@]|$(stylesheetdir)|g' \
        -e 's|@sysconfdir[@]|$(sysconfdir)|g' \
        -e 's|@tooldir[@]|$(tooldir)|g' \
        -e 's|@webroot[@]|$(webroot)|g' \
        -e 's|@webrootdir[@]|$(webrootdir)|g'

CLEANFILES = $(cheetah_TEMPLATES) $(EDITFILES)

$(cheetah_TEMPLATES): %.py: %.tmpl
	$(CHEETAH) compile $<

all: $(cheetah_TEMPLATES)

$(EDITFILES): Makefile
	rm -f $@ $@.tmp
	srcdir=''; \
	  test -f ./$@.in || srcdir=$(srcdir)/; \
	  $(edit) $${srcdir}$@.in >$@.tmp
	mv $@.tmp $@

$(EDITFILES): %: $(srcdir)/%.in
