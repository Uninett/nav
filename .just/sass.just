# Frontend SASS/CSS recipes

[private]
default:
    @just --list sass --unsorted

# Build CSS (production)
build: clean
    #!/usr/bin/env bash
    if [ -f package-lock.json ]; then
        npm ci && npm run build:sass
    else
        npm install && npm run build:sass
    fi

# Watch SASS files for changes (development)
watch:
    npm run watch:sass

# Remove compiled CSS
clean:
    rm -rf python/nav/web/static/css
