#!/usr/bin/env sh
# Second step in vagrant provisioning
# Should be run as vagrant user inside the vm.

[ ! -d .env ] && virtualenv --no-site-packages ~vagrant/.env
. ~vagrant/.env/bin/activate

if [ -f ~vagrant/.bash_profile ]; then
  echo "~vagrant/.bash_profile already modified, rm ~vagrant/.bash_profile if need to reprovision it"
else
  cat << EOF >> ~vagrant/.bash_profile
export DJANGO_SETTINGS_MODULE="nav.django.settings"
export PYTHONPATH="/vagrant/python:$PYTHONPATH"
export PATH="/vagrant/bin:$PATH"
alias rs="django-admin.py runserver 0.0.0.0:8080"
source ~vagrant/.env/bin/activate
EOF
fi

export PYTHONPATH="/vagrant/python:$PYTHONPATH"

pip install -r /vagrant/tools/vagrant-requirements.txt
pip install -r /vagrant/tests/requirements.txt
sudo gem install sass

cd /vagrant
./autogen.sh
./configure NAV_USER="vagrant" --prefix /vagrant --localstatedir ~vagrant/var --sysconfdir ~vagrant/etc --datadir $PWD
cd /vagrant/python
make

if [ "$1" != 0 ]; then
  cd /vagrant/etc
  make
  make install
  sed -e 's/^#\s*\(DJANGO_DEBUG.*\)$/\1/' -i ~vagrant/etc/nav.conf # Enable django debug.
  sed -e 's/userpw_nav=.*/userpw_nav=nav/g' -i ~vagrant/etc/db.conf # Set nav as password.
  cd /vagrant
  make installdirs-local
fi
