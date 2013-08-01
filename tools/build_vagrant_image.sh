#!/bin/bash -e
# Builds a basic debian wheezy base image to be used
# with vagrant. 
#
# Based on http://stacktoheap.com/blog/2013/06/19/building-a-debian-wheezy-vagrant-box-using-veewee/
# :-) 

unset rvm_bin_path
unset GEM_HOME
unset IRBRC
unset MY_RUBY_HOME
unset rvm_path
unset rvm_prefix
unset rvm_version

BASE_DIR=$(dirname $0)
BASE_FULL_DIR=$( cd $(dirname $0) ; pwd -P )
RVM_PATH="$BASE_FULL_DIR/.rvm"
export rvm_path=$RVM_PATH
if [ ! -d $RVM_PATH ]; then
	\curl -L https://get.rvm.io | bash -s stable --ignore-dotfiles --autolibs=read-fail --path $RVM_PATH 
fi
# We'll source it manually .. 
source $RVM_PATH/scripts/rvm

# rvm install failing? Check with   rvm requirements  for missing requirements!

rvm install 1.9.2

if [ ! -d $BASE_DIR/veewee ]; then
	# todo: fork repository due to warning below? :-)
	git clone https://github.com/jedi4ever/veewee.git 
	rvm rvmrc warning ignore $BASE_FULL_DIR/veewee/.rvmrc
	cd $BASE_DIR/veewee
else
	rvm rvmrc warning ignore $BASE_FULL_DIR/veewee/.rvmrc
	cd $BASE_DIR/veewee
	git checkout master
fi

rvm use 1.9.2@veewee --create
gem install bundler
bundle install

# Want other templates? Keep this command commented
# so we don't forget how to check for new templates in the future. 
#bundle exec veewee vbox templates | grep -i debian

bundle exec veewee vbox define 'debian-7.1.0' 'Debian-7.1.0-amd64-netboot' --force

bundle exec veewee vbox build 'debian-7.1.0' --workdir=$BASE_FULL_DIR/veewee --force

bundle exec veewee vbox export 'debian-7.1.0' --force
