#!/bin/sh
# Provision script for vagrant
# Installs system dependent libraries and tools
#
# Invokes tools/vagrant-provision-user.sh as vagrant user

export DEBIAN_FRONTEND=noninteractive

apt-get -y update
apt-get -y build-dep -y psycopg2 python-lxml librrd-dev python-imaging
apt-get -y install mercurial subversion python-virtualenv build-essential autoconf postgresql-client cricket libapache2-mod-wsgi postgresql-9.1 librrd-dev libsnmp15

IS_INSTALLED=$( (test -f ~vagrant/nav_installed); echo $?)

su -l -c "/usr/bin/env sh /vagrant/tools/vagrant-provision-user.sh $IS_INSTALLED" vagrant

if [ $IS_INSTALLED != 0 ]; then
  su -l -c "sh /vagrant/tools/vagrant-provision-postgres.sh" postgres || exit 1
  su -l -c "touch ~vagrant/nav_installed" vagrant || exit 2
fi
