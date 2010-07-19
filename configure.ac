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
tooldir='${sysconfdir}/toolbox'
docdir='${prefix}/doc'
crondir='${sysconfdir}/cron.d'
VERSION=VERSION_NUMBER
if test -z "$CRICKETDIR"; then
	CRICKETDIR='${prefix}/cricket/cricket'
fi


AC_CONFIG_FILES([
	Makefile
	doc/Makefile
	etc/Makefile
	sql/Makefile
	java/Makefile
	templates/Makefile
	python/Makefile
	bin/Makefile
	media/Makefile
	subsystem/ipdevpoll/Makefile
	subsystem/mailin/Makefile
	subsystem/radius/src/Makefile
        subsystem/radius/Makefile
	subsystem/seeddb/Makefile
	subsystem/seeddb/src/Makefile
	subsystem/statTools/Makefile
	subsystem/statTools/sortedStats/Makefile
	subsystem/statemon/Makefile
	subsystem/status/Makefile
	subsystem/thresholdMon/Makefile
	subsystem/useradmin/Makefile
])
AC_OUTPUT
