#!/bin/sh
# Relativt komplisert script på grunn av at java-prosessen kan henge seg opp,
# og da må den drepes - men kun hvis den har gjort seg ferdig, som indikert
# med job-finished filen.

NAV_ROOT="/usr/local/nav"
#NAV_ROOT="/home/kristian/devel/navme"

NAV_CONF="$NAV_ROOT/local/etc/conf/nav.conf"

if [ "$JAVA_HOME" == "" ]; then
        JAVA_HOME=`awk -F= '/JAVA_HOME/ && $1!~/#.*/{gsub("[\t ]", "", $2); print $2}' $NAV_CONF`
fi

CLASSPATH=./getPortData.jar:$NAV_ROOT/navme/java/lib/postgre.jar:$NAV_ROOT/navme/java/lib/snmp.jar:.

CUR_DIR=$NAV_ROOT/navme/cron/getPortData
JOB_FINISHED=$CUR_DIR/job-finished

LOG_DIR="$NAV_ROOT/local/log/getPortData"
#LOG_DIR=$CUR_DIR

COUNT=`ps wwwwx|grep "getPortData"|grep -v getPortData.sh|grep -v grep|wc -l|sed s/" "//g`
if [ "$COUNT" = "0" ] || [ -a $JOB_FINISHED ]; then
        cd $CUR_DIR
        if [ -a $JOB_FINISHED ]; then
                # Must kill old script
                kill -9 `cat last.pid`
                rm -f $JOB_FINISHED
        fi
        # Now run new script
        $JAVA_HOME/bin/java -cp $CLASSPATH getPortData $1 > "$LOG_DIR/getPortData-`/bin/date +%Y-%m-%d_%H-%M`.log" &
        PID="$!"
        echo $PID >last.pid
        wait $PID
        if [ -a $JOB_FINISHED ]; then
                rm -f $JOB_FINISHED
        fi
else
        # echo "getPortData already running (and not finished)"
	echo -n ""
fi
