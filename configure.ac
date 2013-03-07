dnl Process this file with GNU autoconf
m4_include([version.m4])
AC_INIT([nav], VERSION_NUMBER)
AC_CONFIG_AUX_DIR(conf)
AM_INIT_AUTOMAKE([foreign])
AC_PREFIX_DEFAULT(/usr/local/nav)
AC_COPYRIGHT([
There are multiple copyright holders to NAV code.  The major copyright holders
are:

Copyright 2002-2013 UNINETT AS
Copyright 1999-2010 Norwegian University of Science and Technology
Copyright 2007-2010 University of Tromsø

See individual source files for more detailed copyright notices.
])

AC_PROG_INSTALL
AM_PATH_PYTHON([2.6])
AC_PATH_PROG(CHEETAH,cheetah)
if test -z "$CHEETAH"; then
  AC_MSG_ERROR([No Cheetah found, you will be unable to build any web templates])
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
webroot='${prefix}/share/htdocs'
webrootdir='${webroot}'
imagedir='${webroot}/images'
javascriptdir='${webroot}/js'
stylesheetdir='${webroot}/style'
pythonlibdir='${libdir}/python'
pythondir='${pythonlibdir}'
djangotmpldir='${libdir}/templates'
initdir='${sysconfdir}/init.d'
tooldir='${sysconfdir}/toolbox'
docdir='${prefix}/doc'
crondir='${sysconfdir}/cron.d'
VERSION=VERSION_NUMBER
if test -z "$CRICKETDIR"; then
	CRICKETDIR='${prefix}/cricket/cricket'
fi

AC_ARG_ENABLE(install-conf,
            [  --disable-install-conf  Do not install config-files from etc/],
            [CONF_FILES="$enableval"],
            [CONF_FILES="yes"])

AC_MSG_RESULT(Install config-files... $CONF_FILES)

AM_CONDITIONAL([INSTALL_CONF], [test "x$CONF_FILES" = "xyes"])

AC_CONFIG_FILES([
    Makefile
    doc/Makefile
    etc/Makefile
    sql/Makefile
    templates/Makefile
    python/Makefile
    bin/Makefile
    media/Makefile
])

AC_OUTPUT
