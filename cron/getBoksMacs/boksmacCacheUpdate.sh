#!/bin/sh
JAVA_HOME=/usr/java/jdk
CLASSPATH=./getBoksMacs.jar:/usr/local/nav/navme/java/lib/postgre.jar:/usr/local/nav/navme/java/lib/snmp.jar:.

COUNT=`ps wwwwx|grep "updateBoksmacCache"|grep -v grep|wc -l|sed s/" "//g`
if [ "$COUNT" = "0" ]; then
#        echo "updateBoksmacCache not running"
        cd /usr/local/nav/navme/cron/getBoksMacs/
        $JAVA_HOME/bin/java -cp $CLASSPATH updateBoksmacCache $1 > "/usr/local/nav/local/log/cam/boksmacCacheUpdate-`/bin/date +%Y-%m-%d_%H-%M`.log"
else
        #echo updateBoksmacCache already running"
        echo -n "test"
fi
