#!/bin/sh
# Relativt komplisert script på grunn av at java-prosessen kan henge seg opp,
# og da må den drepes - men kun hvis den har gjort seg ferdig, som indikert
# med job-finished filen.

JAVA_HOME=/usr/java/jdk
CLASSPATH=./getBoksMacs.jar:/usr/local/nav/navme/java/lib/postgre.jar:/usr/local/nav/navme/java/lib/snmp.jar:.

NAV_ROOT="/usr/local/nav/navme"
#NAV_ROOT="/home/kristian/devel/navme"

CUR_DIR=$NAV_ROOT/cron/getBoksMacs
JOB_FINISHED=$CUR_DIR/job-finished

LOG_DIR="/usr/local/nav/local/log/cam"
#LOG_DIR=$CUR_DIR

COUNT=`ps wwwwx|grep "getBoksMacsMulti"|grep -v getBoksMacs.sh|grep -v grep|wc -l|sed s/" "//g`
if [ "$COUNT" = "0" ] || [ -a $JOB_FINISHED ]; then
        cd $CUR_DIR
        if [ -a $JOB_FINISHED ]; then
                # Must kill old script
                kill -9 `cat last.pid`
                rm -f $JOB_FINISHED
        fi
        # Now run new script
        $JAVA_HOME/bin/java -cp $CLASSPATH getBoksMacsMulti $1 > "$LOG_DIR/getBoksMacs-`/bin/date +%Y-%m-%d_%H-%M`.log" &
        PID="$!"
        /bin/echo $PID >last.pid
        wait $PID
        if [ -a $JOB_FINISHED ]; then
                rm -f $JOB_FINISHED
        fi
else
        echo "getBoksMacsMulti already running (and not finished)"
fi
