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
  NAV_USER=${USER:-nav}
  NAV_CONF="${NAV_CONFIG_DIR}/nav.conf"
  NAV_UPLOAD_DIR="${UV_PROJECT_ENVIRONMENT}/var/nav/uploads"
  mkdir -p "$NAV_UPLOAD_DIR"
  echo "Updating $NAV_CONF"
  sed -i "s/^NAV_USER=.*/NAV_USER=${NAV_USER}/" "$NAV_CONF"
  sed -i '/^#DJANGO_DEBUG=True/s/^#//' "$NAV_CONF" || echo "DJANGO_DEBUG=True" >> "$NAV_CONF"
  sed -i "s,^#UPLOAD_DIR=.*,UPLOAD_DIR=${NAV_UPLOAD_DIR}," "$NAV_CONF" || echo "UPLOAD_DIR=${NAV_UPLOAD_DIR}" >> "$NAV_CONF"
}

nav config install "$NAV_CONFIG_DIR"
update_nav_conf
update_nav_db_conf

# Ensure the default virtualenv is in the secure_path when running sudo
echo "Defaults        secure_path=\"${UV_PROJECT_ENVIRONMENT}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"" | sudo tee /etc/sudoers.d/secure_path_virtualenv
# Install an empty crontab to avoid the error "no crontab for vscode"
echo -n | crontab
