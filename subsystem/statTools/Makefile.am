include $(top_srcdir)/common.mk

SUBDIRS = sortedStats

bin_SCRIPTS = cleanrrds.py mcc.py migrate_cricket.py extract_cricket_oids.py
sysconf_DATA = cricket-views.conf mcc.conf
tool_DATA = stats.tool
nobase_python_PYTHON = $(wildcard nav/*.py nav/mcc/*.py nav/rrd/*.py)

cron_DATA = cron.d/cricket
EDITFILES = $(cron_DATA)

nobase_doc_DATA = $(wildcard cricket/* cricket/*/* cricket/*/*/*)

