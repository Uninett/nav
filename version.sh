#!/bin/sh
# Update the package version number
GIT=`which git`

show_help() {
    cat <<EOF
$0 [-h] [-r]

This script is used to bump NAV version numbers.

Options:

  -h   Print this help.
  -t   Sets and git-tags a production version from the
       latest changelog entry
EOF
}

in_git_repo() {
  test -e .git && test -x "$GIT"
}

do_describe() {
  ${GIT} describe --tags
}

get_version() {
    do_describe
}

get_version_from_changelog() {
    head CHANGES | awk '/^Version/ { print $2 }'
}

git_tag_exists() {
    local tag="$1"
    ${GIT} rev-parse "$tag" >/dev/null 2>/dev/null
}

tag_from_changelog() {
    local version=$(get_version_from_changelog)
    if [ -z "$version" ]; then
        >&2 echo "Could not get version from changelog"
        exit 1
    elif ! in_git_repo; then
	>&2 echo "I would have tagged ${version}, but I'm not in a Git repository"
	exit 2
    elif git_tag_exists "${version}"; then
	>&2 echo "Cannot tag ${version}, tag already exists:\n"
	${GIT} tag -v "$version"
	exit 3
    else
        echo "Tagging version ${version}"
    fi
    ${GIT} tag --annotate --sign -m "Tag release ${version}" "$version"
    ${GIT} tag -v "$version"
}

# Parse options
OPTIND=1
while getopts "hdt" opt; do
    case "$opt" in
    h)
        show_help
        exit 0
        ;;
    t)  tag_from_changelog
        exit 0
        ;;
    esac
done

# If we got this far, just print the current version
get_version
