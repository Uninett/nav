#!/bin/sh
# Provision script for vagrant
# Installs system dependent libraries and tools
#
# Invokes tools/vagrant-provision-user.sh as vagrant user

export DEBIAN_FRONTEND=noninteractive

apt-get -y update
apt-get -y --no-install-recommends build-dep -y python-psycopg2 python-lxml \
 librrd-dev python-imaging python-ldap
apt-get -y --no-install-recommends install mercurial subversion python-virtualenv build-essential \
 autoconf postgresql-client libapache2-mod-wsgi postgresql-9.1 \
 librrd-dev libsnmp15 git-core python-dev automake rubygems

IS_INSTALLED=$( (test -f ~vagrant/nav_installed); echo $?)

cut=$(which cut)
echo=$(which echo)

# Files in vagrant.d/ is shell provisioning scripts and _should_ follow
# this strict syntax:
#
# <execution order>-<executed as user in vm>-<script name>
#     [0-9][0-9]u?         [a-zaZ]*            [a-zaZ]*
#
# examples:
#
# 10-vagrant-node.bash
# 15u-foo.sh
# 15-vagrant-user.sh
# 20-postgres-postgresql.sh
#
# NOTE: the suffix of 'u' after execution order means this is a user provided
# script which is not added in NAVs repository! Here you can provide your own
# customizations which _should_ not be added to NAVs repository as we're having
# a .hgignore entry for [0-9][0-9]u* files in vagrant.d!
# Here you can provision your setup of your favorite editor etc.

for p in /vagrant/tools/vagrant.d/[0-9]*; do
  full_script=$(basename $p)
  script_tmp=${full_script%.*}
  script_language=${full_script##*.} # Extention on script.
  script_user=$($echo $script_tmp | $cut -f2 -d'-')
  script_name=$($echo $script_tmp | $cut -f3 -d'-')
  echo "[NAV] Running $full_script as $script_user"
  su -l -c "$p $IS_INSTALLED" $script_user
done
