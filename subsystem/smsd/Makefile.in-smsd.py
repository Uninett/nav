#! /usr/bin/env make
# -*- coding: ISO8859-1 -*-
#
# Copyright 2006 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Stein Magnus Jodal <stein.magnus@jodal.no>
#

# Programs
INSTALL = @INSTALL@

# Paths
prefix = @prefix@
exec_prefix = @exec_prefix@
libdir = @libdir@
pythonlibdir = @pythonlibdir@
bindir = @bindir@
sysconfdir = @sysconfdir@
initdir = @initdir@
localstatedir = @localstatedir@

INITFILES =
BINS = smsd.py
LIBS =
CONFFILES =

.PHONY: install-lib install-bin install-conf

all:
lib:
bin:
conf:

install: install-lib install-bin

install-lib: lib
	for file in nav/smsd/*.py; do $(INSTALL) -v -D -m 644 $$file $(DESTDIR)$(pythonlibdir)/$$file || exit 1; done

install-bin: bin
	for file in $(BINS); do $(INSTALL) -v -D -m 755 $$file $(DESTDIR)$(bindir)/$$file || exit 1; done
	for file in $(INITFILES); do $(INSTALL) -v -D -m 755 $$file $(DESTDIR)$(initdir)/$$file	|| exit 1; done

install-conf: conf
	@for file in $(CONFFILES); do
		target=$(DESTDIR)$(sysconfdir)/$$file
		if [ -f "$$target" ]; then
			echo Skipping installation of config file $$file
		else
			$(INSTALL) -v -D -m 644 $$file $$target || exit 1;
		fi
	done

uninstall:
	for file in $(BINS); do rm -f $(DESTDIR)$(bindir)/$$file; done
	rm -rf $(DESTDIR)$(pythonlibdir)
	rm -rf $(DESTDIR)$(pythonlibdir)

clean:
	find -name *.pyc -print0 | xargs -0 rm -f

distclean: clean
	find -name '*~' -print0 | xargs -0 rm -f
	rm Makefile
