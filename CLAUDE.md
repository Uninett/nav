# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NAV (Network Administration Visualized) is an enterprise network monitoring and management system developed since 1999. It monitors network infrastructure, discovers topology, tracks devices/users, and provides alerting via email/SMS/Slack.

**Tech Stack:** Python 3.9+, Django 4.2-5.2, PostgreSQL, Twisted (async), SNMP (pynetsnmp-2), NAPALM

## Common Commands

### Testing

**Unit tests** (`tests/unittests/`) - No database access, must use mocks for DB/external dependencies:
```bash
pytest tests/unittests/
pytest tests/unittests/ipdevpoll/interfaces_test.py
pytest tests/unittests/ipdevpoll/interfaces_test.py::test_function_name
pytest tests/unittests --cov=python/nav --cov-report=html  # with coverage
```

Use `@pytest.mark.twisted` for async tests.

**Integration tests** (`tests/integration/`) - Have database access, can test endpoints and send requests.

**Functional tests** (`tests/functional/`) - Selenium browser tests.

Integration and functional tests must run inside the test Docker container:
```bash
cd tests/docker && make && make shell
# Inside container:
tox run -e integration-py311-django42
tox run -e functional-py311-django42
tox -e javascript
```

### Linting & Formatting

```bash
ruff format python/ tests/              # Format code
ruff check python/ tests/               # Lint code
ruff check --fix python/ tests/         # Auto-fix lint issues
pre-commit run --all-files              # Run all pre-commit hooks
```

Install pre-commit hooks (auto-formats on commit):
```bash
pip install pre-commit && pre-commit install
```

### Building

```bash
# Development installation
pip install -e ".[dev,test]"

# Build SASS/CSS
npm install && npm run build:sass
# or: make sassbuild

# Watch SASS for changes
npm run watch:sass

# Build documentation
make doc
# or: sphinx-build doc/ doc/_build/
```

### Database

```bash
# Apply schema migrations
navsyncdb
```

## Architecture

### Directory Structure

```
python/nav/
├── bin/              # CLI entry points (daemons, utilities)
├── models/           # Django ORM models
│   └── sql/          # Raw SQL schema (baseline/) and migrations (changes/)
├── web/              # Django web apps (40+ apps)
│   ├── templates/    # Django HTML templates
│   ├── static/       # JS, CSS, images
│   └── sass/         # SCSS source files
├── ipdevpoll/        # Device polling framework with plugin architecture
├── eventengine/      # Event correlation and processing
├── alertengine/      # Alert generation and dispatch
├── snmptrapd/        # SNMP trap handling
└── mibs/             # SNMP MIB definitions
```

### Core Components

1. **Data Collection Layer** - Background daemons (`ipdevpolld`, `snmptrapd`, `statemon`, `macwatch`)
2. **Event Processing** - `eventengine` correlates events, `alertengine` dispatches notifications
3. **Web/API Layer** - Django apps provide REST API and web UI
4. **Database** - PostgreSQL with namespaces: `manage` (core), `profiles` (users), `logger`, `arnold`, `radius`

### Plugin Architecture

ipdevpoll uses plugins in `python/nav/ipdevpoll/plugins/` for device data collection (SNMP, ARP, LLDP, CDP, etc.).

### Schema Changes (Important Django Divergence)

NAV uses custom SQL migrations, **not Django migrations** - this is the biggest divergence from standard Django conventions:
1. Create `python/nav/models/sql/changes/sc.<major>.<minor>.<point>.sql`
2. Run `navsyncdb` to apply
3. Update corresponding Django models in `python/nav/models/`

## Code Style

- PEP 8 via Ruff (auto-formatted)
- Line length: 88 characters
- Pre-commit hooks enforce formatting
- GPL v3 license header required on new files
- **Import ordering**: Modules must be alphabetically ordered, AND named imports within each import statement must also be alphabetic (e.g., `from module import A, B, C`)
- **Test naming**: Use `test_when_<condition>_then_it_should_<expected_behavior>` pattern

## Contributing

- Sign CLA via GitHub CLA Assistant on PR
- Base feature branches on `master`, bug fixes on `X.Y.x` release branches
- Add changelog entry in `changelog.d/` using towncrier format: `<issue>.{added,changed,fixed,removed,deprecated,security}.md`

## Development Environment

**Devcontainers (recommended)** - Most developers use devcontainers in PyCharm or VS Code due to the many required components. See `doc/hacking/using-devcontainers.rst`.

Alternative: Docker Compose setup in `doc/hacking/using-docker.rst`.

## Current Development Focus

The codebase is undergoing modernization, with emphasis on replacing JavaScript with HTMX (django-htmx) for interactive UI elements.

## Key Configuration Files

- `nav.conf` - Main NAV configuration
- `db.conf` - Database connection settings
- `logging.conf` - Logging configuration
- `ipdevpoll.conf` - Device polling configuration
