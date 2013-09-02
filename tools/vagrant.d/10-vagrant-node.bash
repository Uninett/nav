#!/usr/bin/env bash
#
curl https://raw.github.com/creationix/nvm/master/install.sh | sh
/usr/bin/env bash
[[ -s /home/vagrant/.nvm/nvm.sh ]] && . /home/vagrant/.nvm/nvm.sh
nvm install 0.10
nvm alias default 0.10
cd /vagrant/htdocs/js
npm install --optional