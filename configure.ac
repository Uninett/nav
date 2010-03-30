dnl Process this file with GNU autoconf
AC_INIT([nav], [3.6])
AC_CONFIG_AUX_DIR(conf)
AM_INIT_AUTOMAKE([foreign])
AC_REVISION($Revision: $)
AC_PREFIX_DEFAULT(/usr/local/nav)

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
AC_SUBST(webapps)
AC_SUBST(webroot)
AC_SUBST(javalibdir)
AC_SUBST(pythonlibdir)
AC_SUBST(perllibdir)
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
webapps='${prefix}/apache/webapps'
webroot='${prefix}/apache/webroot'
pythonlibdir='${libdir}/python'
javalibdir='${libdir}/java'
perllibdir='${libdir}/perl'
djangotmpldir='${libdir}/templates'
initdir='${sysconfdir}/init.d'
tooldir='${prefix}/apache/tools'
docdir='${prefix}/doc'
crondir='${sysconfdir}/cron.d'
VERSION=`cat VERSION`
if $GREP -q devel VERSION && ! test -z "$HG" && test -e .hg
then
	VERSION=`$HG identify -i`
fi
if test -z "$CRICKETDIR"; then
	CRICKETDIR='${prefix}/cricket/cricket'
fi


AC_OUTPUT(Makefile
	doc/Makefile
	src/Makefile
	src/build.properties
	src/eventEngine/eventEngine.sh
	src/eventEngine/eventengine
	src/getBoksMacs/getBoksMacs.sh
	src/getDeviceData/getDeviceData
	src/getDeviceData/getDeviceData.sh
	src/networkDiscovery/networkDiscovery.sh
	subsystem/alertengine/Makefile
	subsystem/alertengine/alertengine
	subsystem/alertprofiles/Makefile
	subsystem/arnold/Makefile
	subsystem/arnold/images/Makefile
	subsystem/arnold/lib/Makefile
	subsystem/dbTools/Makefile
	subsystem/devicehistory/Makefile
	subsystem/ipdevinfo/Makefile
	subsystem/ipdevpoll/Makefile
	subsystem/ipinfo/Makefile
	subsystem/ipinfo/templates/Makefile
	subsystem/l2trace/Makefile
	subsystem/l2trace/src/Makefile
	subsystem/lib-perl/Makefile
	subsystem/lib-python/Makefile
	subsystem/logger/Makefile
	subsystem/logger/bin/Makefile
	subsystem/logger/conf/Makefile
	subsystem/logger/src/Makefile
	subsystem/logger/templates/Makefile
	subsystem/machinetracker/Makefile
	subsystem/machinetracker/src/Makefile
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
	subsystem/smsd/smsd
	subsystem/snmptrapd/Makefile
	subsystem/snmptrapd/snmptrapd
	subsystem/startstop/Makefile
	subsystem/startstop/functions
	subsystem/statTools/Makefile
	subsystem/statTools/sortedStats/Makefile
	subsystem/statemon/Makefile
	subsystem/statemon/pping
	subsystem/statemon/servicemon
	subsystem/status/Makefile
	subsystem/thresholdMon/Makefile
	subsystem/useradmin/Makefile
	subsystem/webfront/Makefile
)

echo
echo "Now run 'make' to build NAV"
