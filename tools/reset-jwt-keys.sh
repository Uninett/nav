#!/bin/sh -e
config_dir=$(dirname $(nav config where))
jwt_conf="${config_dir}/webfront/jwt.conf"
key_file=/tmp/jwtRS256.key
pubkey_file=/tmp/jwtRS256.key.pub

echo "This script will overwrite existing NAV JWT signing keys and re-configure the [nav] section of ${jwt_conf}"
read -p "Continue? (y/n): " continue
case $continue in
    [Yy]* ) ;;
    * ) echo "Aborted."; exit 1;;
esac

echo "Generating new RSA keys.."
openssl genrsa -out "${key_file}" 4096
openssl rsa -in "${key_file}" -pubout -outform PEM -out "${pubkey_file}"

echo "Updating [nav] section of ${jwt_conf} ..."
uvx crudini --set "${jwt_conf}" nav private_key "${key_file}"
uvx crudini --set "${jwt_conf}" nav public_key "${pubkey_file}"
uvx crudini --set "${jwt_conf}" nav name "localhost"
uvx crudini --set "${jwt_conf}" nav access_token_lifetime "1h"
uvx crudini --set "${jwt_conf}" nav refresh_token_lifetime "1d"

echo "Please restart the web server to ensure changes take effect"
