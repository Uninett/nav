#!/bin/sh -e

show_help() {
    cat <<EOF
$0 [-r revision]

Simple shell script to create and sign tarball source distribution of NAV

Invocation with no arguments will create a tarball from the HEAD of the
current repository.
EOF
}

REVISION=$(git describe)

# Parse arguments
OPTIND=1
while getopts "hr:" opt; do
    case $opt in
        h) show_help
           exit 0;
           ;;
        r) REVISION="$OPTARG"
           ;;
        *)
            show_help >&2
            exit 1
            ;;
    esac
done

DIST_NAME="nav-$REVISION"
TARBALL="${DIST_NAME}.tar.gz"

archive() {
    umask 0022
    git rev-parse "$REVISION" >/dev/null || return 1
    git archive --format=tar --prefix="$DIST_NAME/" "$REVISION" \
        | gzip - > "$TARBALL"
}

if [ -f $TARBALL ]; then
    echo "Tarball already exists: $TARBALL"
    echo "Please remove it."
    exit 1
fi

echo "Exporting archive of NAV revision $REVISION ..."
if archive; then
    echo "MD5SUM:"; md5sum "$TARBALL"
    echo "SHA1SUM:"; sha1sum "$TARBALL"

    echo "Please sign the tarball"
    gpg --armor --detach-sign "$TARBALL"

    echo "All done.  Enjoy your tarball:."
    ls -la "$TARBALL"*
fi
