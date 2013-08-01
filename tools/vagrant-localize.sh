#!/bin/sh 

FULL_PATH=$( cd $(dirname $0) ; pwd -P)
HG_ROOT=$( cd $FULL_PATH/.. ; pwd -P)

cd $HG_ROOT

export DEBIAN_FRONTEND=noninteractive

MIRROR=$(grep -o -m1 -E "(ftp|http)://(ftp|http)\...\.debian.org" /etc/apt/sources.list)
echo $MIRROR
vagrant ssh -c "sudo sed -e \"s#\(ftp\|http\)://\(ftp\|http\)\...\.debian.org#$MIRROR#g\" -i /etc/apt/sources.list"

debconf-get-selections  | grep -E "(keyboard-configuration)" | vagrant ssh -- "sudo debconf-set-selections"
vagrant ssh -c "sudo dpkg-reconfigure -f noninteractive keyboard-configuration"

cat /etc/timezone | vagrant ssh -- "sudo tee /etc/timezone"
vagrant ssh -c "sudo dpkg-reconfigure -f noninteractive tzdata"

cd -
