#!/bin/bash

set -ex

# Ensure latest NAV code is built
mydir=$(dirname $0)
"$mydir/build.sh"
cd /source


django-admin check && exec django-admin runserver --insecure 0.0.0.0:8080
