#!/bin/sh
# Second step in vagrant provisioning
# Should be run as vagrant user inside the vm.

[ ! -d .env ] && virtualenv --no-site-packages ~vagrant/.env
. ~vagrant/.env/bin/activate

if [ -f ~vagrant/.bash_profile ]; then
  echo "~vagrant/.bash_profile already modified, rm ~vagrant/.bash_profile if need to reprovision it"
else
  cat << EOF >> ~vagrant/.bash_profile
export WEBROOTDIR=/vagrant/media
export DJANGOTMPLDIR=/vagrant/templates
export DJANGO_SETTINGS_MODULE="nav.django.settings"
export PYTHONPATH="/vagrant/python:$PYTHONPATH"
export PATH="/vagrant/bin:$PATH"
source ~/.env/bin/activate
EOF
fi

export PYTHONPATH="/vagrant/python:$PYTHONPATH"

pip install -vv -r /vagrant/tools/vagrant-requirements.txt
pip install -v -r /vagrant/tools/vagrant-requirements2.txt # Silly modules who can't be installed in same process as rest of em..

cd /vagrant
./autogen.sh
./configure --prefix /vagrant --localstatedir ~vagrant/var --sysconfdir ~vagrant/etc WEBROOTDIR=/vagrant/media DJANGOTMPLDIR=/vagrant/templates
cd /vagrant/python
make

if [ $1 != 0 ]; then
  cd /vagrant/etc
  make
  make install
  sed -e 's/^#\s*\(DJANGO_DEBUG.*\)$/\1/' -i ~vagrant/etc/nav.conf # Enable django debug.
  sed -e 's/userpw_nav=.*/userpw_nav=nav/g' -i ~vagrant/etc/db.conf # Set nav as password.
  cd /vagrant
  make installdirs-local
fi
