#!/usr/bin/env bash

prefix=/usr/local/nav
exec_prefix=${prefix}
bindir=${exec_prefix}/bin
localstatedir=${prefix}/var
sysconfdir=${prefix}/etc
libdir=${exec_prefix}/lib
javalibdir=${libdir}/java

NAV_CONF="${sysconfdir}/nav.conf"

if test -z "$JAVA_HOME"; then 
    JAVA_HOME=`awk -F= '/JAVA_HOME/ && $1!~/#.*/{gsub("[\t ]", "", $2); print $2}' $NAV_CONF`
fi

CUR_DIR=${javalibdir}/networkDiscovery
LOG_DIR="${localstatedir}/log/networkDiscovery"
OUTLOG=${LOG_DIR}/networkDiscovery.html
ERRLOG=${LOG_DIR}/networkDiscovery-stderr.log

# If error log exists and has content, we rename it before creating a
# new one
if [ -s ${ERRLOG} ]; then
    newname="${ERRLOG}.`date +'%Y-%m-%d-%H%M'`.log"
    mv ${ERRLOG} ${newname}
fi

cd $CUR_DIR
# Run script
$JAVA_HOME/bin/java -Xmx268435456 -cp "networkDiscovery.jar:$CLASSPATH" networkDiscovery $1 > ${OUTLOG} 2> ${ERRLOG}
