SUBDIRS = templates

pathmodule = nav/buildconf.py
nobase_python_DATA = $(wildcard nav/*.py) $(wildcard nav/*/*.py) $(wildcard nav/*/*/*.py) $(pathmodule)
bin_SCRIPTS = bin/hasPrivilege.py

CLEANFILES = $(pathmodule)

$(pathmodule): Makefile
	@echo "Generating $(pathmodule) ..."
	@echo "# This file was generated during NAV build" > $(pathmodule)
	@echo "prefix=\"$(prefix)\"" >> $(pathmodule)
	@echo "exec_prefix=\"$(exec_prefix)\"" >> $(pathmodule)
	@echo "bindir=\"$(bindir)\"" >> $(pathmodule)
	@echo "libdir=\"$(libdir)\"" >> $(pathmodule)
	@echo "pythonlibdir=\"$(pythonlibdir)\"" >> $(pathmodule)
	@echo "sysconfdir=\"$(sysconfdir)\"" >> $(pathmodule)
	@echo "localstatedir=\"$(localstatedir)\"" >> $(pathmodule)
	@echo "webroot=\"$(webroot)\"" >> $(pathmodule)
	@echo "initdir=\"$(initdir)\"" >> $(pathmodule)
	@echo "djangotmpldir=\"$(djangotmpldir)\"" >> $(pathmodule)
	@echo "VERSION=\"$(VERSION)\"" >> $(pathmodule)

