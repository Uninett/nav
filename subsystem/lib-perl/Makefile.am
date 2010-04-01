pathmodule = NAV/Path.pm
nobase_perllib_DATA = NAV.pm $(pathmodule)

CLEANFILES = $(pathmodule)

$(pathmodule): $(pathmodule).source
	$(top_srcdir)/tools/expand.pl $(pathmodule).source > $(pathmodule)
