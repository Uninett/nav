# Documentation recipes — Sphinx build, watch, and tox

[private]
default:
    @just --list doc --unsorted

# Generate alert types reference and build Sphinx docs
build:
    uv run python doc/exts/alerttypes.py > doc/reference/alerttypes.rst
    uv run sphinx-build doc/ build/sphinx/html/

# Build docs in an isolated tox environment
tox:
    uv run tox -e docs

# Watch doc/ for changes and rebuild (requires inotifywait)
watch:
    @while inotifywait -e modify -e move -e create -e delete -r --exclude \# doc/ NOTES.rst; do \
        uv run sphinx-build doc/ build/sphinx/html/; \
    done
