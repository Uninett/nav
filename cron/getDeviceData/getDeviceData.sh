#!/bin/sh
# Relativt komplisert script på grunn av at java-prosessen kan henge seg opp,
# og da må den drepes - men kun hvis den har gjort seg ferdig, som indikert
# med job-finished filen.

NAV_ROOT="/usr/local/nav"

NAV_CONF="$NAV_ROOT/local/etc/conf/nav.conf"

if [ "$JAVA_HOME" == "" ]; then
	JAVA_HOME=`awk -F= '/JAVA_HOME/ && $1!~/#.*/{gsub("[\t ]", "", $2); print $2}' $NAV_CONF`
fi

CUR_DIR=$NAV_ROOT/navme/cron/getBoksMacs
LOG_DIR="$NAV_ROOT/local/log/cam"

COUNT=`ps wwwwx|grep "getDeviceData"|grep -v getDeviceData.sh|grep -v grep|wc -l|sed s/" "//g`
if [ "$COUNT" == "0" ]; then
        cd $CUR_DIR
        # Run script
        # $JAVA_HOME/bin/java -jar getDeviceData.jar $1 > "$LOG_DIR/getDeviceData-`/bin/date +%Y-%m-%d_%H-%M`.log" &
        $JAVA_HOME/bin/java -jar getDeviceData.jar $1
else
        echo "getDeviceData already running!"
	# echo -n ""
fi
