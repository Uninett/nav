#!/bin/sh
# Relativt komplisert script på grunn av at java-prosessen kan henge seg opp,
# og da må den drepes - men kun hvis den har gjort seg ferdig, som indikert
# med job-finished filen.

#NAV_ROOT="/usr/local/nav"
NAV_ROOT="/home/kristian/devel"

NAV_CONF="$NAV_ROOT/local/etc/conf/nav.conf"

if [ "$JAVA_HOME" == "" ]; then
	JAVA_HOME=`awk -F= '/JAVA_HOME/ && $1!~/#.*/{gsub("[\t ]", "", $2); print $2}' $NAV_CONF`
fi

CUR_DIR=$NAV_ROOT/navme/cron/getBoksMacs
JOB_FINISHED=$CUR_DIR/job-finished

LOG_DIR="$NAV_ROOT/local/log/cam"
#LOG_DIR=$CUR_DIR

COUNT=`ps wwwwx|grep "getBoksMacs"|grep -v getBoksMacs.sh|grep -v grep|wc -l|sed s/" "//g`
if [ "$COUNT" == "0" ] || [ -a $JOB_FINISHED ]; then
        cd $CUR_DIR
        if [ -a $JOB_FINISHED ]; then
                # Must kill old script
                kill -9 `cat last.pid`
                rm -f $JOB_FINISHED
                sleep 2
                COUNT=`ps wwwwx|grep "getBoksMacs"|grep -v getBoksMacs.sh|grep -v grep|wc -l|sed s/" "//g`
        fi

        # Check again that getBoksMacs is not already running
        if [ "$COUNT" == "0" ]; then
                # Now run script
                $JAVA_HOME/bin/java -jar getBoksMacs.jar $1 > "$LOG_DIR/getBoksMacs-`/bin/date +%Y-%m-%d_%H-%M`.log" &
                PID="$!"
                echo $PID >last.pid
                wait $PID
                if [ -a $JOB_FINISHED ]; then
                        rm -f $JOB_FINISHED
                fi
        else
                echo "ERROR, kill -9 of previous getBoksMacs failed!"
        fi
else
        # echo "getBoksMacsMulti already running (and not finished)"
	echo -n ""
fi
