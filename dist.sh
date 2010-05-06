#!/bin/sh

# Simple shell script to create a tarball source distribution of NAV

USAGE="dist.sh [-r revision]

Invokation with no arguments will create a tarball from the tip of the
current repository."

REVISION=tip
DIST_SANDBOX=.dist_sandbox

# Parse arguments
ARG_PREV=""
for ARG in $@
do
  if [ "$ARG_PREV" ]; then

    case $ARG_PREV in
         -r)  REVISION="$ARG" ;;
          *)  ARG_PREV=$ARG ;;
    esac

    ARG_PREV=""

  else

    case $ARG in
      -r)
        ARG_PREV=$ARG
        ;;
      *)
        echo " $USAGE"
        exit 1
        ;;
    esac
  fi
done

DIST_NAME="nav-$REVISION"
TARBALL="${DIST_NAME}.tar.gz"

if [ -e $DIST_SANDBOX ]; then
    echo "Sandbox directory already exists: $DIST_SANDBOX"
    echo "Please remove it."
    exit 1
fi
if [ -f $TARBALL ]; then
    echo "Tarball already exists: $TARBALL"
    echo "Please remove it."
    exit 1
fi

mkdir $DIST_SANDBOX && cd $DIST_SANDBOX || exit 1

echo "Exporting archive of NAV revision $REVISION ..." 
hg archive -r $REVISION -X '.hg*' $DIST_NAME
if [ $? -eq 0 ]; then
    # Generate the ./configure script before creating the tarball
    cp ../version.m4 $DIST_NAME
    cd $DIST_NAME
    ./autogen.sh
    cd ..

    echo "Creating tarball ($TARBALL) ..."
    tar czf $TARBALL $DIST_NAME

    echo "md5sum:"
    md5sum $TARBALL
    echo "sha1sum:"
    sha1sum $TARBALL

    mv $TARBALL ..
    cd ..
    echo "Removing sandbox directory ..."
    rm -rf $DIST_SANDBOX

    echo "All done.  Enjoy your tarball."
fi
