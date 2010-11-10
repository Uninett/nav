dnl Process this file with GNU autoconf
m4_include([version.m4])
AC_INIT([nav], VERSION_NUMBER)
AC_CONFIG_AUX_DIR(conf)
AM_INIT_AUTOMAKE([foreign])
AC_PREFIX_DEFAULT(/usr/local/nav)
AC_COPYRIGHT([
Copyright belongs to various parties for different parts of NAV:
Part copyright 1999-2008 Norwegian University of Science and Technology
Part copyright 2002-2010 UNINETT AS
Part copyright various contributors, see individual files.
])

AC_PROG_INSTALL
AM_PATH_PYTHON([2.4])
AC_PATH_PROG(CHEETAH,cheetah)
if test -z "$CHEETAH"; then
  AC_MSG_ERROR([No Cheetah found, you will be unable to build any web templates])
fi
AC_PATH_PROG(ANT,ant)
if test -z "$ANT"; then
  AC_MSG_ERROR([No Ant found, you need this to build java software])
fi
AC_PATH_PROG(SED, sed)
AC_PATH_PROG(GREP, grep)
AC_PATH_PROG(HG, hg)

AC_SUBST(nav_user)
AC_SUBST(webroot)
AC_SUBST(webrootdir)
AC_SUBST(imagedir)
AC_SUBST(javascriptdir)
AC_SUBST(stylesheetdir)
AC_SUBST(javalibdir)
AC_SUBST(pythonlibdir)
AC_SUBST(djangotmpldir)
AC_SUBST(initdir)
AC_SUBST(tooldir)
AC_SUBST(docdir)
AC_SUBST(crondir)
AC_SUBST(VERSION)
dnl The location of the cricket binaries
AC_ARG_VAR(CRICKETDIR,The directory containing the Cricket executables)

dnl Setting some default variables for NAV
nav_user=navcron
webroot='${prefix}/apache/webroot'
webrootdir='${webroot}'
imagedir='${webroot}/images'
javascriptdir='${webroot}/js'
stylesheetdir='${webroot}/style'
pythonlibdir='${libdir}/python'
pythondir='${pythonlibdir}'
javalibdir='${libdir}/java'
djangotmpldir='${libdir}/templates'
initdir='${sysconfdir}/init.d'
tooldir='${prefix}/apache/tools'
docdir='${prefix}/doc'
crondir='${sysconfdir}/cron.d'
VERSION=VERSION_NUMBER
if test -z "$CRICKETDIR"; then
	CRICKETDIR='${prefix}/cricket/cricket'
fi


AC_CONFIG_FILES([
	Makefile
	doc/Makefile
	src/Makefile
	subsystem/alertengine/Makefile
	subsystem/alertprofiles/Makefile
	subsystem/arnold/Makefile
	subsystem/arnold/config/Makefile
	subsystem/dbTools/Makefile
	subsystem/devicehistory/Makefile
	subsystem/geomap/Makefile
	subsystem/geomap/media/Makefile
	subsystem/ipdevinfo/Makefile
	subsystem/ipdevinfo/config/Makefile
	subsystem/ipdevinfo/templates/Makefile
	subsystem/ipdevpoll/Makefile
	subsystem/l2trace/Makefile
	subsystem/lib-python/Makefile
	subsystem/lib-python/templates/Makefile
	subsystem/logger/Makefile
	subsystem/machinetracker/Makefile
	subsystem/mailin/Makefile
	subsystem/maintenance/Makefile
	subsystem/messages/Makefile
	subsystem/netmap/Makefile
	subsystem/networkexplorer/Makefile
	subsystem/radius/src/Makefile
        subsystem/radius/Makefile
	subsystem/report/Makefile
	subsystem/seeddb/Makefile
	subsystem/seeddb/src/Makefile
	subsystem/smsd/Makefile
	subsystem/snmptrapd/Makefile
	subsystem/startstop/Makefile
	subsystem/statTools/Makefile
	subsystem/statTools/sortedStats/Makefile
	subsystem/statemon/Makefile
	subsystem/status/Makefile
	subsystem/thresholdMon/Makefile
	subsystem/useradmin/Makefile
	subsystem/webfront/Makefile
	subsystem/webfront/media/Makefile
])
AC_OUTPUT
