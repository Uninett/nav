# NAV Development Command Runner
# https://just.systems/man/

mod test      '.just/test.just'
mod doc       '.just/doc.just'
mod sass      '.just/sass.just'
mod changelog '.just/changelog.just'
mod docker    '.just/docker.just'
mod db        '.just/db.just'

# Default: list available recipes
[private]
default:
    @just --list --unsorted

# ─── Setup ────────────────────────────────────────────────────────────────────

# Install all Python dependencies
[group('setup')]
sync:
    uv sync --all-extras --all-groups

# Install pre-commit hooks
[group('setup')]
setup-hooks:
    uvx pre-commit install

# Install Playwright browsers (default: chromium)
[group('setup')]
setup-playwright browsers="chromium":
    uv run playwright install --with-deps {{ browsers }}

# Full development setup (dependencies, hooks, frontend)
[group('setup')]
setup: sync setup-hooks
    npm ci

# ─── Code Quality ────────────────────────────────────────────────────────────

# Format code with ruff (e.g., just format --check)
[group('quality')]
format *args:
    uv run ruff format {{ args }} .

# Lint with ruff (e.g., just lint --fix)
[group('quality')]
lint *args:
    uv run ruff check {{ args }} .

# Run pre-commit hooks on staged files (e.g., just check --all-files)
[group('quality')]
check *args:
    uv run pre-commit run {{ args }}

# ─── Django ──────────────────────────────────────────────────────────────────

# Run a Django management command
[group('django')]
manage *args:
    uv run django-admin {{ args }}

# Run Django system check
[group('django')]
django-check:
    uv run django-admin check --fail-level=ERROR

# Start Django development server
[group('django')]
serve host="0.0.0.0" port="8080":
    uv run django-admin runserver {{ host }}:{{ port }}

# ─── Cleaning ────────────────────────────────────────────────────────────────

# Remove Python build artifacts
[group('clean')]
clean:
    find . -name '__pycache__' -print0 | xargs -0 rm -rf 2>/dev/null || true
    find . -name '*.pyc' -print0 | xargs -0 rm -rf 2>/dev/null || true
    find . -name '*.egg-info' -print0 | xargs -0 rm -rf 2>/dev/null || true
    rm -rf build/ dist/

# Remove tox, docs, CSS, and all build artifacts
[group('clean')]
[confirm("This will remove .tox, doc/_build, and compiled CSS. Continue?")]
distclean: clean sass::clean
    rm -rf .tox
    rm -rf doc/_build

# ─── CI ──────────────────────────────────────────────────────────────────────

# Run all CI checks locally (formatting, linting, changelog, tests)
ci: (format "--check") lint changelog::check test::all
