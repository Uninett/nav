#!/bin/sh

NAV_ROOT="/usr/local/nav"
NAV_CONF="$NAV_ROOT/local/etc/conf/nav.conf"

if [ "$JAVA_HOME" == "" ]; then
        JAVA_HOME=`awk -F= '/JAVA_HOME/ && $1!~/#.*/{gsub("[\t ]", "", $2); print $2}' $NAV_CONF`
fi

CONF_FILE="$NAV_ROOT/local/etc/conf/navAdmin.conf"
NAVME_ROOT="$NAV_ROOT/navme"
CUR_DIR=$NAVME_ROOT/subsystem/navAdmin
REPORT_DIR=$NAV_ROOT/local/log/navAdmin/report

cd $CUR_DIR
$JAVA_HOME/bin/java -jar NavUtils.jar $CONF_FILE -avledTopologi > "$REPORT_DIR/avledTopologi.html"
