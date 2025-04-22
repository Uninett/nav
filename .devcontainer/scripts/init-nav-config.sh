#!/bin/bash
NAV_CONFIG_DIR="$UV_PROJECT_ENVIRONMENT/etc/nav"

update_nav_db_conf() {
    # Update db config
    DB_CONF="${NAV_CONFIG_DIR}/db.conf"
    echo "Updating $DB_CONF"
    cat > "$DB_CONF" <<EOF
dbhost=${PGHOST:-db}
dbport=${PGPORT:-5432}
db_nav=${PGDATABASE:-nav}
script_default=${PGUSER:-nav}
userpw_${PGUSER:-nav}=${PGPASSWORD:-nav}
EOF
}

update_nav_conf() {
  NAV_USER=${_REMOTE_USER:-nav}
  NAV_CONF="${NAV_CONFIG_DIR}/nav.conf"
  echo "Updating $NAV_CONF"
  sed -i "s/^NAV_USER=.*/NAV_USER=${NAV_USER}/" "$NAV_CONF"
  sed -i '/^#DJANGO_DEBUG=True/s/^#//' "$NAV_CONF" || echo "DJANGO_DEBUG=True" >> "$NAV_CONF"
}

mkdir -p /usr/share/nav/var/uploads && chown "${_REMOTE_USER}" /usr/share/nav/var/uploads
nav config install "$NAV_CONFIG_DIR"
update_nav_conf
update_nav_db_conf
