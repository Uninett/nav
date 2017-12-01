#!/bin/sh -xe
uid=$(id -u)
BUILDDIR=${BUILDDIR:-/opt/nav}

echo "Building and installing NAV..."
make distclean || true
./version.sh -d  # set a dev version number
./autogen.sh
./configure --prefix "${BUILDDIR}" NAV_USER=build
make
gosu root:root make install
gosu root:root chown -R $uid "${BUILDDIR}/var" "${BUILDDIR}/etc"

# Make Python libraries available for everyone
gosu root:root ln -fs "${BUILDDIR}/lib/python/nav" $(python -c 'import site;print(site.getsitepackages()[0])')

# Since we're testing, let's debug log everything we can
cat > "${BUILDDIR}/etc/logging.conf" <<EOF
[levels]
root=DEBUG
EOF
echo "DJANGO_DEBUG=True" >> "${BUILDDIR}/etc/nav.conf"


# Now, because of a stupid Python issue, the running uid needs a passwd entry
# Reference: https://bugs.python.org/issue10496
if ! whoami; then
    echo "Modifying the internal build user's UID"
    gosu root usermod -u "$uid" build
fi
