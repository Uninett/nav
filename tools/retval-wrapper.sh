#!/bin/sh
# Hack to work around psql's lack of proper return values.
# Used in tests to check if creation and upgrade of db works.

# Create file to store output
out=`mktemp`

# Try running whatever command we were given
$@ 2>&1 | tee $out

# Check result and return status
retval=`grep ERROR $out | wc -l`
rm $out
exit $retval
