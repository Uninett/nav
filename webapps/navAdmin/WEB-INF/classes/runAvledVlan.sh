#!/bin/sh

JAVA_HOME=/usr/java/jdk
CLASSPATH=./getPortData.jar:/usr/local/nav/navme/java/lib/postgre.jar:/usr/local/nav/navme/java/lib/snmp.jar:.

CONF_FILE="/usr/local/nav/local/etc/conf/navAdmin.conf"

NAV_ROOT="/usr/local/nav"

NAVME_ROOT="$NAV_ROOT/navme"
#NAVME_ROOT="/home/kristian/devel/navme"

CUR_DIR=$NAVME_ROOT/webapps/navAdmin/WEB-INF/classes

REPORT_DIR=$NAV_ROOT/local/log/navAdmin/report

cd $CUR_DIR
$JAVA_HOME/bin/java -cp $CLASSPATH NavUtils $CONF_FILE -avledVlan > "$REPORT_DIR/avledVlan.html"
