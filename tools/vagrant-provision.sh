#!/bin/sh


export DEBIAN_FRONTEND=noninteractive

apt-get -y update
apt-get -y build-dep -y psycopg2 python-lxml librrd-dev python-imaging
apt-get -y install mercurial subversion python-virtualenv build-essential autoconf postgresql-client cricket libapache2-mod-wsgi postgresql-9.1 librrd-dev libsnmp15

su -c "createuser -d -R -S nav || true" postgres
su -c "psql -U postgres -c \"ALTER USER nav WITH PASSWORD 'nav'\"" postgres
su -c "createdb -O nav nav || true" postgres

su -l vagrant
[ ! -d .env ] && virtualenv --no-site-packages ~vagrant/.env
. ~vagrant/.env/bin/activate

if [ -f ~vagrant/modified_bash ]; then
  echo "~vagrant/.bashrc already modified, rm ~vagrant/modified_bash if need to reprovision it"
else
  cat << EOF >> ~vagrant/.bashrc
export WEBROOT=/vagrant/media
export DJANGO_SETTINGS_MODULE="nav.django.settings"
export PYTHONPATH="/vagrant/python:$PYTHONPATH"
source ~/.env/bin/activate
EOF
  touch ~vagrant/modified_bash
fi

export PYTHONPATH="/vagrant/python:$PYTHONPATH"

pip install -vv -r /vagrant/tools/vagrant-requirements.txt
pip install -v -r /vagrant/tools/vagrant-requirements2.txt # Silly modules who can't be installed in same process as rest of em..

cd /vagrant
sed -e 's/^#\s*\(DJANGO_DEBUG.*\)$/\1/' -i etc/nav.conf # Enable django debug. 
sed -e 's/userpw_nav=.*/userpw_nav=nav/g' -i etc/db.conf # Set nav as password. 
./autogen.sh
./configure --prefix /vagrant WEBROOT=/vagrant/media
cd /vagrant/python 
make
cd /vagrant/etc
make
/vagrant/sql/syncdb.py 
