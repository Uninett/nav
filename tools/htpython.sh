#!/bin/bash
#
# This script takes a path to the NAV webroot on the commandline.
# It will find all .htaccess files in the web directory hierarchy that
# contain "SetHandler python-path", and make sure the PythonPath
# variable in those are set correctly.
#

webroot=${1-$PWD}
prefix=${2-/usr/local/nav/apache/webroot}

echo Working from $webroot
cd $webroot
candidates=`find . -name '.htaccess' -type f -printf "%P\00" | xargs -0 grep -li "SetHandler.*python-program"`
for cand in $candidates; do
  ppath="PythonPath \"sys.path+['${prefix}/`dirname ${cand}`']\""
  if grep -iq "^PythonPath" ${cand}; then
      perl -pi -e "s%^PythonPath.*$%${ppath}%i" ${cand} && echo Replaced ${ppath}
  else
      echo ${ppath} >> ${cand} && echo Added ${ppath}
  fi
done
