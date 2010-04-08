include $(top_srcdir)/common.mk

tool_DATA = machinetracker.tool
sysconf_DATA = machinetracker.conf

cheetah_TEMPLATES = MachineTrackerTemplate.py
cheetahdir = $(pythondir)/nav/web/templates
nobase_cheetah_PYTHON = $(cheetah_TEMPLATES)

mywebdir = $(webrootdir)/machinetracker
myweb_DATA = .htaccess
myweb_PYTHON = machinetracker.py

