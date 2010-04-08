include $(top_srcdir)/common.mk

SUBDIRS = sortedStats

bin_SCRIPTS = cleanrrds.pl makecricketconfig.pl
sysconf_DATA = cricket-views.conf
tool_DATA = stats.tool
nobase_python_PYTHON = $(wildcard nav/*.py nav/rrd/*.py)

cron_DATA = cron.d/cricket
EDITFILES = $(cron_DATA)

nobase_doc_DATA = $(wildcard cricket/* cricket/*/* cricket/*/*/* cricket/cricket-config/.nav cricket/cricket-config/*/.nav)

