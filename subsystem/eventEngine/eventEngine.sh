#!/bin/bash

NAV_ROOT="/usr/local/nav"

NAV_CONF="$NAV_ROOT/local/etc/conf/nav.conf"

if [ "$JAVA_HOME" == "" ]; then
  JAVA_HOME=`awk -F= '/JAVA_HOME/ && $1!~/#.*/{gsub("[\t ]", "", $2); print $2}' $NAV_CONF`
fi

CUR_DIR=$NAV_ROOT/navme/subsystem/eventEngine

LOG_DIR="$NAV_ROOT/local/log"

COUNT=`ps wwwwx|grep "eventEngine.jar"|grep -v eventEngine.sh|grep -v grep|wc -l|sed s/" "//g`
if [ "$COUNT" == "0" ]; then
        cd $CUR_DIR
        # Now run script
        $JAVA_HOME/bin/java -jar eventEngine.jar $1 >> "$LOG_DIR/eventEngine.log" 2> error-log &
        PID="$!"
        echo $PID >$NAV_ROOT/local/var/run/eventEngine.pid
else
        echo -n "eventEngine already running"
        exit 1
fi

exit 0
