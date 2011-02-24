#!/bin/sh
test -d conf || mkdir conf
./version.sh ; aclocal && automake -ac && autoconf
