#!/usr/bin/env python3
#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Generate or verify the committed OpenAPI schema snapshot.

The snapshot lives at :file:`doc/api/openapi.yml`. With no arguments this script
rewrites that snapshot from the current code. With ``--check`` it instead fails
(non-zero exit, printing a diff) if the committed snapshot is out of date, which
is how CI guards against the snapshot drifting away from the code.

The ``version`` field of the spec is derived from NAV's scm version, which
varies by environment: a tagged checkout yields the release version
(e.g. ``5.18.2``), while an untagged or shallow clone (as on CI for fork pull
requests) falls back to a setuptools_scm guess like ``0.1.dev1+g<hash>``. To
keep the snapshot reproducible regardless of scm state, the version value is
normalized to a fixed placeholder before writing or comparing. The live schema
served at runtime still reports the real version.
"""

import argparse
import difflib
import os
import re
import sys
import tempfile
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parent.parent / "doc" / "api" / "openapi.yml"

# Matches the whole spec version line, whatever scm-derived value it holds.
_VERSION_LINE = re.compile(r'(?m)^  version: .*$')

# Fixed placeholder written into the snapshot in place of the scm version, so
# the committed file is identical across tagged and untagged checkouts.
_PLACEHOLDER_VERSION = "  version: 0.0.0"


def normalize(schema: str) -> str:
    """Replace the scm-derived spec version with a fixed placeholder."""
    return _VERSION_LINE.sub(_PLACEHOLDER_VERSION, schema, count=1)


def ensure_config():
    """Make sure NAV can find its config files, installing examples if needed."""
    if os.environ.get("NAV_CONFIG_DIR"):
        return
    config_dir = Path(tempfile.mkdtemp(prefix="nav_openapi_config_"))
    os.environ["NAV_CONFIG_DIR"] = str(config_dir)

    from nav.config import install_example_config_files

    install_example_config_files(str(config_dir))


def generate() -> str:
    """Return the normalized OpenAPI schema for the current code."""
    ensure_config()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nav.django.settings")

    import django

    django.setup()

    from drf_spectacular.renderers import OpenApiYamlRenderer
    from drf_spectacular.generators import SchemaGenerator

    generator = SchemaGenerator()
    schema = generator.get_schema(request=None, public=True)
    rendered = OpenApiYamlRenderer().render(schema, renderer_context={})
    return normalize(rendered.decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the committed snapshot is out of date instead of writing it.",
    )
    args = parser.parse_args()

    generated = generate()

    if args.check:
        current = SNAPSHOT.read_text() if SNAPSHOT.exists() else ""
        if current != generated:
            diff = difflib.unified_diff(
                current.splitlines(keepends=True),
                generated.splitlines(keepends=True),
                fromfile=f"{SNAPSHOT} (committed)",
                tofile="generated from code",
            )
            sys.stderr.writelines(diff)
            sys.stderr.write(
                f"\n\nERROR: {SNAPSHOT} is out of date. "
                "Regenerate it with:\n\n    python tools/openapi_schema.py\n\n"
            )
            return 1
        print(f"{SNAPSHOT} is up to date.")
        return 0

    SNAPSHOT.write_text(generated)
    print(f"Wrote {SNAPSHOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
