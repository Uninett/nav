#!/bin/sh
#
# Create local directory structure for NAV
# Should be run from /usr/local/nav
# $Id: mklocal.sh,v 1.3 2002/07/23 10:04:53 mortenv Exp $
#
mkdir -p local/
mkdir -p local/apache
mkdir -p local/apache/pic
mkdir -p local/apache/pub
mkdir -p local/apache/res
mkdir -p local/apache/res/pic/ragen/bildetekst
mkdir -p local/apache/res/pic/ragen/overskrift
mkdir -p local/apache/sec
mkdir -p local/apache/vhtdocs
mkdir -p local/apache/htpasswd
mkdir -p local/etc
mkdir -p local/etc/conf
mkdir -p local/etc/conf/live
mkdir -p local/etc/conf/varsel
mkdir -p local/etc/conf/syslog
mkdir -p local/etc/conf/ragen
mkdir -p local/etc/kilde
mkdir -p local/etc/htpasswd
mkdir -p local/log
mkdir -p local/etc/htpasswd
mkdir -p local/log/live
mkdir -p local/log/trapdetect
mkdir -p local/log/varsel
mkdir -p local/log/cam
mkdir -p local/log/navAdmin
mkdir -p local/log/navAdmin/report
mkdir -p local/log/getPortData
mkdir -p local/log/syslog
mkdir -p local/log/arp
mkdir -p local/log/collect
mkdir -p local/cricket
mkdir -p local/cricket/cricket-data
mkdir -p local/cron
mkdir -p local/bin
mkdir -p local/pg_backup
mkdir -p local/log/varsel
mkdir -p local/var/run

touch local/log/varsel/servicelog
touch local/log/alarm
touch local/log/alarm2
touch local/log/syslog/cisco.log
