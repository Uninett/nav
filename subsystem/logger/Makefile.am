include $(top_srcdir)/common.mk

mywebdir = $(webrootdir)/logger
tool_DATA = logger.tool
cron_DATA = logengine
myweb_DATA = .htaccess
myweb_PYTHON = loggerhandler.py
cheetah_TEMPLATES = nav/web/templates/LoggerTemplate.py
nobase_python_DATA = $(wildcard nav/*.py) $(cheetah_TEMPLATES)
bin_SCRIPTS = bin/logengine.py

config = conf/logger.conf
EDITFILES = $(config) $(cron_DATA)
sysconf_DATA = $(config)

