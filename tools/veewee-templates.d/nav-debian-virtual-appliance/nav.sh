# Set up NAV

date > /etc/nav_box_build_time

# Customize the message of the day
echo 'Welcome to Network Administration Visualized virtual appliance.' > /etc/motd.tail

gpg --keyserver keys.gnupg.net --recv-keys 0xC3DE75AE036BAB8D # Morten Werner Forsbring <werner@debian.org>
gpg --armor --export 0xC3DE75AE036BAB8D | sudo apt-key add -

echo "deb http://pkg-nav.alioth.debian.org/debian/ squeeze local" > /etc/apt/sources.list.d/nav.list

export DEBIAN_FRONTEND=noninteractive

random_pass=$(gpg -a --gen-random 1 12)

debconf-set-selections <<EOF
nav	nav/dbpass	password	$random_pass
nav	nav/db_purge	boolean	false
nav	nav/db_generation	boolean	true
nav	nav/apache2_restart	boolean	true
nav	nav/db_auto_update	boolean	true
EOF

apt-get -y update
apt-get -y --no-install-recommends install nav

a2dissite default
a2dissite default-ssl
a2ensite nav-default
/etc/init.d/apache2 force-reload

NAV_CRICKET_CONFIG=/etc/nav/cricket-config
sed -e "s/\$gConfigRoot.*/\$gConfigRoot = '${NAV_CRICKET_CONFIG}';/" -i /etc/cricket/cricket-conf.pl

# Disable system default cricket cron job. 
sed -e 's$\(\*/5 \* \* \* \*[ \t]*cricket\)$#\1$g' -i /etc/cron.d/cricket

# Rename default alias from /cricket to /cricket-orig
sed -e 's$\(Alias /cricket\)\(.*\)\( /usr/share/cricket\)$\1-orig\3$g' -i/etc/apache2/conf.d/cricket

NAV_CRICKET_LOG=/var/log/nav/cricket
sed -e "s|\$gLogDir.*|\$gLogDir = '$NAV_CRICKET_LOG'|g" -i /etc/cricket/cricket-conf.pl

su - -c cricket-compile navcron
su - -c /usr/lib/nav/mcc.py navcron

# Enable NAV at start up
sed -e s/RUN_NAV=[01]*$/RUN_NAV=1/g /etc/default/nav

/etc/init.d/nav restart

