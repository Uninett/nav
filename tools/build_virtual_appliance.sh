#!/usr/bin/env bash

# Builds a virtual appliance in OVF format out of NAV, based on Debian Wheezy
# and the latest available NAV Debian package.
#
# If ovftool is available, the OVF will additionally be converted to VMWare
# format.

debian='nav-debian-virtual-appliance'

BASE_FULL_DIR=$( cd $(dirname $0) ; pwd -P )

. rvm_and_veewee_install.sh 

source $BASE_FULL_DIR/rvm_activate

test -z "$BASE_FULL_DIR" && exit 1
test -z "$debian" && exit 2

tmp_dir="$BASE_FULL_DIR/veewee/$debian"

[ ! -d $BASE_FULL_DIR/veewee ] && echo "You must run rvm_and_veewee_install.sh first as you need veewee!" && exit 1
cd $BASE_FULL_DIR/veewee

[ ! -d $BASE_FULL_DIR/veewee/definitions ] && mkdir $BASE_FULL_DIR/veewee/definitions
ln -sf $BASE_FULL_DIR/veewee-templates.d/$debian $BASE_FULL_DIR/veewee/definitions/$debian

[ -d $tmp_dir ] && rm -f $tmp_dir/*{.vmdk,ovf,Vagrantfile}
[ ! -d $tmp_dir ] && mkdir $tmp_dir

bundle exec veewee vbox build "$debian" --force

bundle exec veewee vbox export "$debian" --force

tar -C $tmp_dir -xvf $debian.box

cd $tmp_dir

OVFTOOL=$(which ovftool)
if [[ -n "$OVFTOOL" ]]; then
    "$OVFTOOL" --lax "${tmp_dir}/box.ovf" "${tmp_dir}/vmware-nav.vmx"
else
    echo "could not find ovftool binary. ovftool must be used if you want"
    echo "to use the resulting OVF image on VMWare"
fi

echo 
echo "Virtual appliance image(s) done for NAV. You find it in $tmp_dir !"
