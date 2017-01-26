#!/bin/sh -e

# Simple shell script to create a tarball source distribution of NAV

USAGE="dist.sh [-r revision]

Invokation with no arguments will create a tarball from the HEAD of the
current repository."

REVISION=$(git describe)

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

if [ -f $TARBALL ]; then
    echo "Tarball already exists: $TARBALL"
    echo "Please remove it."
    exit 1
fi

echo "Exporting archive of NAV revision $REVISION ..." 
if git archive --format=tar --prefix="$DIST_NAME/" "$REVISION" | tar x; then
    # Do the magic dance required to get a few generated files into the
    # archive
    ./autogen.sh
    cp version.m4 "$DIST_NAME/"
    ( cd "$DIST_NAME" && ./autogen.sh )

    echo "Creating tarball ($TARBALL) ..."
    tar czf "$TARBALL" "$DIST_NAME"

    rm -rf "$DIST_NAME"
    
    echo "md5sum:"
    md5sum "$TARBALL"
    echo "sha1sum:"
    sha1sum "$TARBALL"

    echo "Please sign the tarball"
    gpg --armor --detach-sign "$TARBALL"
    
    echo "All done.  Enjoy your tarball:."
    ls -la "$TARBALL"*
fi
