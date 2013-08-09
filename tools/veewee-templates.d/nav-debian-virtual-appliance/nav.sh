# Set up Vagrant.

date > /etc/nav_box_build_time


echo "deb http://pkg-nav.alioth.debian.org/debian/ squeeze local" > /etc/apt/sources.list.d/nav

export DEBIAN_FRONTEND=noninteractive

apt-get -y update
apt-get -y --no-install-recommends install nav

# Customize the message of the day
echo 'Welcome to Network Administration Visualized virtual appliance.' > /var/run/motd

