# Set up NAV

date > /etc/nav_box_build_time

# Customize the message of the day
echo 'Welcome to Network Administration Visualized virtual appliance.' > /etc/motd.tail

apt-get install -y apt-transport-https
apt-key adv --keyserver keys.gnupg.net --recv-key 0xC9F583C2CE8E05E8 # UNINETT NAV APT repository

echo "deb https://nav.uninett.no/debian/ wheezy nav navbeta" > /etc/apt/sources.list.d/nav.list

export DEBIAN_FRONTEND=noninteractive

random_pass=$(gpg -a --gen-random 1 12)

debconf-set-selections <<EOF
nav	nav/dbpass	password	$random_pass
nav	nav/db_purge	boolean	false
nav	nav/db_generation	boolean	true
nav	nav/apache2_restart	boolean	true
nav	nav/db_auto_update	boolean	true
nav	nav/cricket_movegiga	boolean	false
EOF

apt-get -y update
apt-get --force-yes -y --no-install-recommends install nav graphite-carbon graphite-web
# Explicitly install rrdtool to enable data migrations from older NAV versions
apt-get --force-yes -y --no-install-recommends install rrdtool python-rrdtool

a2dissite default
a2dissite default-ssl
a2ensite nav-default

# Ensure Carbon's UDP listener is enabled, and that Carbon doesn't initially
# limit the amount of new whisper files that can be created per minute.
CARBONCONF="/etc/carbon/carbon.conf"
sed -e 's/^MAX_CREATES_PER_MINUTE\b.*$/MAX_CREATES_PER_MINUTE = inf/g' -i "$CARBONCONF"
sed -e 's/^ENABLE_UDP_LISTENER\b.*$/ENABLE_UDP_LISTENER = True/g' -i "$CARBONCONF"

# enable carbon-cache start at boot time
sed -e 's/^CARBON_CACHE_ENABLED\b.*$/CARBON_CACHE_ENABLED=true/g' -i /etc/default/graphite-carbon

# Initialize graphite-web database
sudo -u _graphite graphite-manage syncdb --noinput

# Configure graphite-web to run openly on port 8000
# WARNING: May be a security risk if port 8000 is exposed outside the virtual
# machine without authorization measures.
cat > /etc/apache2/sites-available/graphite-web <<EOF
Listen 8000
<VirtualHost *:8000>

	WSGIDaemonProcess _graphite processes=1 threads=1 display-name='%{GROUP}' inactivity-timeout=120 user=_graphite group=_graphite
	WSGIProcessGroup _graphite
	WSGIImportScript /usr/share/graphite-web/graphite.wsgi process-group=_graphite application-group=%{GLOBAL}
	WSGIScriptAlias / /usr/share/graphite-web/graphite.wsgi

	Alias /content/ /usr/share/graphite-web/static/
	<Location "/content/">
		SetHandler None
	</Location>

	ErrorLog \${APACHE_LOG_DIR}/graphite-web_error.log

	# Possible values include: debug, info, notice, warn, error, crit,
	# alert, emerg.
	LogLevel warn

	CustomLog \${APACHE_LOG_DIR}/graphite-web_access.log combined

</VirtualHost>

EOF
a2ensite graphite-web

# Configure carbon according to NAV's wishes
cp /etc/nav/graphite/*.conf /etc/carbon/

apache2ctl restart

# Enable NAV at start up
echo "Enable NAV to run at start up"
sed -e s/RUN_NAV=[01]*$/RUN_NAV=1/g -i /etc/default/nav

/etc/init.d/nav restart
/etc/init.d/nav stop
