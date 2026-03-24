# Changelog management via towncrier

[private]
default:
    @just --list changelog --unsorted

# Check that changelog entries exist (as CI does)
check:
    uv run towncrier check --compare-with origin/master

# Create a changelog entry (types: security, removed, deprecated, added, changed, fixed)
create issue type message:
    uv run towncrier create -c "{{ message }}" {{ issue }}.{{ type }}.md

# Build the changelog (for releases)
build:
    uv run towncrier build --yes
