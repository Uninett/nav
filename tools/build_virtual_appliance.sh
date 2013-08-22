#!/usr/bin/env bash
# Build virtual appliance of NAV in virtualbox format
# and also exports a vmware format from the ovf. 


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

# Change memory from 256MB to 2048MB
sed -e 's#256 MB of memory#2048 MB of memory#' -i box.ovf
line_number_memory=$(grep -n -A4 '2048 MB of memory' box.ovf | grep VirtualQuantity | sed 's/^\([0-9]\+\).*$/\1/')
sed -e "${line_number_memory}s/256/2048/" -i box.ovf
echo "Changed memory from 256 MB to 2048 MB in .ovf template."

ovftool --lax $tmp_dir/box.ovf $tmp_dir/vmware-nav.vmx

echo 
echo "Virtual appliance image(s) done for NAV. You find it in $tmp_dir !"
