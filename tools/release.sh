#!/bin/sh

# Simple shell script to tag a NAV release on a series branch and
# create a tarball source distribution of it

USAGE="Usage: 

  release.sh <version>

This script assumes the current working directory is inside a NAV
series branch, preferably updated to the repository tip.  It will
update the VERSION file, tag the resulting changeset with <version>,
close the release head and create a tarball from the tag.

The script has no error handling.  If things get out of hand, 'hg
strip' is your friend.
"

VERSION="$1"
if [ -z "$VERSION" ]; then
    echo "$USAGE"
    exit 1
fi

ROOT=$(hg root)

cd $ROOT
if [ -f VERSION ]; then
    echo "Creating release version $VERSION"
    echo "$VERSION" > VERSION
    # Commit VERSION file
    hg commit -m"Bump version number to $VERSION" VERSION
    # Update to parent changeset and set the tag
    hg up -r -2
    hg tag -r tip "$VERSION"
    # Start closing the release head
    hg merge -r -2
    # Don't leave the VERSION file changed on the new branch head
    hg revert -r tip VERSION
    hg commit -m"Close $VERSION release head"
    echo "Version created"
    # Show the history we just created
    hg glog -l4
    echo "Making tarball"
    ./dist.sh -r "$VERSION"
fi
