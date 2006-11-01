#!/bin/sh
# This script will output a shell command to set a proper CLASSPATH for
# building autodiscovery The classpath will include the existing classpath from
# the shell environment, and the build directories of the dependencies within
# the NAV source tree (which means you must build the NAV Java code first)
#
# To use the script, eval its output, like so:
#
#  eval `gen-classpath.sh`


DEPS="SimpleSnmp Util ConfigParser Database NetboxInfo Eventi Logger"
SRC=../../src
CP=$CLASSPATH

SRC=`(cd $SRC;pwd)`
for DEP in $DEPS
do
	DEPPATH=$SRC/$DEP/build
	CP=$CP:$DEPPATH
done
echo export CLASSPATH=$CP

