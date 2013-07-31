#!/bin/sh -x
#
# Installs rvm, veewee to build vagrant images and make a debian image

# rvm
# bash -s stable --path=/...         
# rvm_path myself + sourcing scripts/rvm 
# https://github.com/wayneeseguin/rvm/issues/2058  
\curl -L https://get.rvm.io | bash -s stable -- --ignore-dotfiles --autolibs=read-fail
# We'll source it manually .. 
source $HOME/.rvm/scripts/rvm
# Rails 1.9.2 as pr veewee documentation
# Note:  rvm requirements   should be installed. 

rvm install 1.9.2

git clone https://github.com/jedi4ever/veewee.git 
cd veewee
rvm use 1.9.2@veewee --create
gem install bundler
bundle install

#bundle exec veewee vbox templates | grep -i debian

bundle exec veewee vbox define 'debian-7.1.0' 'Debian-7.1.0-amd64-netboot'

bundle exec veewee vbox build 'debian-7.1.0'

bundle exec veewee vbox export 'debian-7.1.0'
