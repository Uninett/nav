#!/bin/bash -e
# Builds a basic debian wheezy base image to be used
# with vagrant. 
#
# Based on http://stacktoheap.com/blog/2013/06/19/building-a-debian-wheezy-vagrant-box-using-veewee/
# :-) 

. rvm_and_veewee_install.sh 

source $BASE_FULL_DIR/rvm_activate

rvm use 1.9.2@veewee --create
# Want other templates? Keep this command commented
# so we don't forget how to check for new templates in the future. 
#bundle exec veewee vbox templates | grep -i debian
bundle exec veewee vbox define 'nav-basevm' 'Debian-7.1.0-amd64-netboot' --force

# Sets the norwegian mirror as default mirror
sed 's#\(d-i.mirror.http.hostname.string\)\(.*\)#\1 ftp.no.debian.org#g' -i $BASE_FULL_DIR/veewee/definitions/nav-basevm/preseed.cfg

bundle exec veewee vbox build 'nav-basevm' --workdir=$BASE_FULL_DIR/veewee --force

bundle exec veewee vbox export 'nav-basevm' --force
