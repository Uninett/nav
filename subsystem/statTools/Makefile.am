SUBDIRS = sortedStats

bin_SCRIPTS = cleanrrds.pl makecricketconfig.pl
sysconf_DATA = cricket-views.conf
tool_DATA = stats.tool
nobase_python_PYTHON = $(wildcard nav/*.py nav/rrd/*.py)

cron_DATA = cron.d/cricket

nobase_doc_DATA = $(wildcard cricket/* cricket/*/* cricket/*/*/* cricket/cricket-config/.nav cricket/cricket-config/*/.nav)


cron.d/cricket: cron.d/cricket.in Makefile
	$(SED) \
	  -e 's|@CRICKETDIR[@]|$(CRICKETDIR)|g' cron.d/cricket.in > cron.d/cricket

