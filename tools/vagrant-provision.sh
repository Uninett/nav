#!/bin/sh


export DEBIAN_FRONTEND=noninteractive

apt-get -y update
apt-get -y build-dep -y psycopg2 python-lxml librrd-dev
apt-get -y install mercurial subversion python-virtualenv build-essential autoconf postgresql-client cricket libapache2-mod-wsgi postgresql-9.1 librrd-dev libsnmp15

virtualenv --no-site-packages .env
. .env/bin/activate

if [ -f ~vagrant/modified_bash ]; then
  echo "~vagrant/.bashrc already modified, rm ~vagrant/modified_bash if need to reprovision it"
else
  cat << EOF >> ~vagrant/.bashrc
export DJANGO_SETTINGS_MODULE="nav.django.settings"
export PYTHONPATH="/vagrant/python:$PYTHONPATH"
source ~/.env/bin/activate
EOF
  touch ~vagrant/modified_bash
fi

pip install -vv -r /vagrant/tools/vagrant-requirements.txt
pip install -v -r /vagrant/tools/vagrant-requirements2.txt # Silly modules who can't be installed in same process as rest of em..
