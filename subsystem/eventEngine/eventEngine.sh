#!/bin/sh

NAV_ROOT="/usr/local/nav"
#NAV_ROOT="/home/kristian/devel"

NAV_CONF="$NAV_ROOT/local/etc/conf/nav.conf"

if [ "$JAVA_HOME" == "" ]; then
	JAVA_HOME=`awk -F= '/JAVA_HOME/ && $1!~/#.*/{gsub("[\t ]", "", $2); print $2}' $NAV_CONF`
fi

CUR_DIR=$NAV_ROOT/navme/subsystem/eventEngine

LOG_DIR="$NAV_ROOT/local/log/eventEngine"
#LOG_DIR=$CUR_DIR

COUNT=`ps wwwwx|grep "eventEngine"|grep -v eventEngine.sh|grep -v grep|wc -l|sed s/" "//g`
if [ "$COUNT" == "0" ]; then
        cd $CUR_DIR
        # Now run script
        $JAVA_HOME/bin/java -jar eventEngine.jar $1 > "$LOG_DIR/eventEngine-`/bin/date +%Y-%m-%d_%H-%M`.log" &
        PID="$!"
        echo $PID >last.pid
        wait $PID
else
        echo "eventEngine already running"
fi
