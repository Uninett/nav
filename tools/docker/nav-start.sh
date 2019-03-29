#!/bin/bash
if [ "$NONAVSTART" -gt 0 ]; then
    echo "NONAVSTART is set, not starting NAV backend processes" >&2
    exit 0
else
    exec nav start
fi
