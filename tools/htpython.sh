#!/usr/bin/env bash
#
# Copyright 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
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
