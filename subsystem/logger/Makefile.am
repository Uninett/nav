include $(top_srcdir)/common.mk

mywebdir = $(webrootdir)/logger
tool_DATA = logger.tool
cron_DATA = logengine
myweb_DATA = .htaccess
myweb_PYTHON = loggerhandler.py
cheetah_TEMPLATES = nav/web/templates/LoggerTemplate.py
nobase_python_DATA = $(cheetah_TEMPLATES)
bin_SCRIPTS = bin/logengine.py

config = conf/logger.conf
CLEANFILES += $(config)
sysconf_DATA = $(config)

$(config): $(config).source Makefile
	$(top_srcdir)/tools/expand.pl $(config).source > $(config)
