#!/bin/sh
test -d conf || mkdir conf
aclocal && automake -ac && autoconf
