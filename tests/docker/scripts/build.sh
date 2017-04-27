#!/bin/sh -xe
uid=$(id -u)
BUILDDIR=${BUILDDIR:-/opt/nav}

echo "Building and installing NAV..."
make distclean || true
./autogen.sh
./configure --prefix "${BUILDDIR}" NAV_USER=build
make
gosu root:root make install
gosu root:root chown -R $uid "${BUILDDIR}/var" "${BUILDDIR}/etc"

# Make Python libraries available for everyone
gosu root:root ln -fs "${BUILDDIR}/lib/python/nav" /usr/local/lib/python2.7/

# Since we're testing, let's debug log everything we can
cat > "${BUILDDIR}/etc/logging.conf" <<EOF
[levels]
root=DEBUG
EOF
