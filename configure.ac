dnl Process this file with GNU autoconf
m4_include([version.m4])
AC_INIT([nav], VERSION_NUMBER)
AC_CONFIG_AUX_DIR(conf)
AM_INIT_AUTOMAKE([foreign])
AC_PREFIX_DEFAULT(/usr/local/nav)
AC_COPYRIGHT([
There are multiple copyright holders to NAV code.  The major copyright holders
are:

Copyright 2002-2014 UNINETT AS
Copyright 1999-2010 Norwegian University of Science and Technology
Copyright 2007-2010 University of Tromsø

See individual source files for more detailed copyright notices.
])

AC_PROG_INSTALL
AM_PATH_PYTHON([2.7])
AC_PATH_PROG(SASS,sass)
if test -z "$SASS"; then
   AC_MSG_ERROR([No sass found. sass is needed to compile style sheets. Install latest sass gem])
fi
AC_PATH_PROG(SED, sed)
AC_PATH_PROG(GREP, grep)
AC_PATH_PROG(HG, hg)

AC_SUBST(nav_user)
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
AC_ARG_VAR(NAV_USER,User to run cronjobs as)

dnl Setting some default variables for NAV
webrootdir='${datadir}/htdocs'
djangotmpldir='${datadir}/templates'
imagedir='${webrootdir}/images'
javascriptdir='${webrootdir}/js'
stylesheetdir='${webrootdir}/style'
pythonlibdir='${libdir}/python'
pythondir='${pythonlibdir}'
initdir='${sysconfdir}/init.d'
tooldir='${sysconfdir}/toolbox'
docdir='${prefix}/doc'
crondir='${sysconfdir}/cron.d'
VERSION=VERSION_NUMBER
if test -z "$NAV_USER"; then
    nav_user=navcron
else
    nav_user=$NAV_USER
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
    htdocs/Makefile
])

AC_OUTPUT
