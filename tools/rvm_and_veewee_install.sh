#!/usr/bin/env bash 
# Install rvm under VCS-ROOT/tools/.rvm and veewee to VCS-ROOT/tools/veewee
#
# Based on http://stacktoheap.com/blog/2013/06/19/building-a-debian-wheezy-vagrant-box-using-veewee/
#
# Note worty comments if your maintaing/hacking on this script:
#
# @mpapis | you can "set -e" after playing with rvm, because rvm disables -e ... 
#   Rockj | hoho :-p
#  Rockj  | shouldn't rvm remember those flags? and set em back afterwards maybe?
#  Rockj  | safe to «set -e» before source $RVM_PATH/scripts/rvm then?
# @mpapis | I would need to play with that idea, but it was like this for long time, it should be safe
#         | now, but it makes no difference, you should set the flag after using rvm
# (since rvm1 is frozed, this is planned to be fixed for rvm2 incase any hacker were wondering... ) 
#
# @mpapis | I do not know python that much, played with it only for short time
#   Rockj | mpapis: you should look into virtualenv, that's python's version of rvm ;)
#   Rockj | but it doesn't accept multiple ruby's tho
#   Rockj | one virtualenv holds one python install you could say
# @mpapis | virtualenv does not install python - that I know ;)
#   Rockj | that's how rvm should be as well
#   Rockj | or can rvm use system ruby?
# @mpapis | it can mount rubies - but it is less safer
# @mpapis | ruby is different and often compiled with some extra flags that makes things a lot harder for
#         | using it in rvm
# @mpapis | rvm2 will be different
# https://docs.google.com/document/d/1xW9GeEpLOWPcddDg_hOPvK4oeLxJmU3Q5FiCNT7nTAc/edit?usp=sharing
#
#
# rvm dependencies:
# sudo apt-get install gawk g++ libreadline6-dev zlib1g-dev libssl-dev libyaml-dev libsqlite3-dev sqlite3 autoconf libgdbm-dev libncurses5-dev automake libtool bison libffi-dev bash curl patch bzip2 ca-certificates gcc make libc6-dev patch openssl ca-certificates libreadline6 curl zlib1g pkg-config 
#
# veewee dependencies:
# sudo apt-get install libxml2-dev libxslt1-dev

# Unload rvm settings if any you have any rvm installed already in $HOME/.rvm ..
if typeset -f __unload_rvm >/dev/null 2>&1 ; then __unload_rvm ; fi

BASE_DIR=$(dirname $0)
BASE_FULL_DIR=$( cd $(dirname $0) ; pwd -P )

if [ ! -f $BASE_FULL_DIR/.rvmtrust ]; then
  echo "You accept that this script does nasty fetching of SOURCES online.."
  echo ".. which includes piping scripts to shell and run installers..."
  echo ".. we've done our best to validate if it is safe..."
  echo ".. but you run this hacker script on your own risk!"
  echo " accept terms?! touch $BASE_FULL_DIR/.rvmtrust"
  exit 1
fi

RVM_PATH="$BASE_FULL_DIR/.rvm"
export rvm_path=$RVM_PATH


# todo:
# fork rvm and use:
# \curl -L 'path to raw installer on company fork' | bash -s branch company/stable ...
# This should feel the script to be more SAFE. 

if [ ! -d $RVM_PATH ]; then
	\curl -L https://get.rvm.io | bash -s stable --ignore-dotfiles --autolibs=read-fail --path $RVM_PATH 
fi
# We'll source it manually .. 
source $BASE_FULL_DIR/rvm_activate
# rvm install failing? Check with   rvm requirements  for missing requirements!

rvm install 1.9.2
if [ ! -d $BASE_DIR/veewee ]; then
	# todo: fork repository due to warning below? :-)
	git clone https://github.com/jedi4ever/veewee.git 
	rvm rvmrc warning ignore $BASE_FULL_DIR/veewee/.rvmrc
	rvm rvmrc trust $BASE_FULL_DIR/veewee/.rvmrc
	cd $BASE_DIR/veewee
else
	rvm rvmrc warning ignore $BASE_FULL_DIR/veewee/.rvmrc
	rvm rvmrc trust $BASE_FULL_DIR/veewee/.rvmrc
	cd $BASE_DIR/veewee
	git checkout master
fi

rvm use 1.9.2@veewee --create
gem install bundler
bundle install
echo "rvm installed under $BASE_FULL_DIR/.rvm"
echo "veewee installed under $BASE_FULL_DIR/veewee"
echo "Before using veewee, make sure you:"
echo "  source $BASE_FULL_DIR/rvm_activate"
echo "and run veewee commands with:"
echo "  cd $BASE_FULL_DIR/veewee"
echo "  bundle veewee ..."
