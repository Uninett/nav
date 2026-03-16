#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Test environment setup helper.

Provides functions to create a temporary NAV config directory and initialize
a test database.
"""

import getpass
import os
import subprocess
import tempfile
from pathlib import Path

# Password used for the NAV admin user during test runs
ADMIN_PASSWORD = "omicronpersei8"


def ensure_config_dir() -> Path:
    """Create a temporary NAV config dir with pristine example configs.

    Sets ``NAV_CONFIG_DIR`` so that all subsequent NAV imports find these
    files.  Returns the path to the new directory.  Idempotent: if a
    config dir has already been created this session (or the environment variable has
    been overridden by the test suite initiator), it is returned as-is.
    """
    existing = os.environ.get("NAV_CONFIG_DIR")
    if existing:
        return Path(existing)

    config_dir = Path(tempfile.mkdtemp(prefix="nav_test_config_"))
    print(f"Using {config_dir} as NAV config directory for this test session.")
    os.environ["NAV_CONFIG_DIR"] = str(config_dir)

    from nav.config import install_example_config_files

    install_example_config_files(str(config_dir))

    _write_db_conf(config_dir)
    _patch_nav_conf(config_dir)
    _patch_graphite_conf(config_dir)
    _refresh_nav_config()
    return config_dir


def create_test_database() -> None:
    """Drop, recreate and populate the NAV test database.

    Expects ``NAV_CONFIG_DIR`` to already be set (done by `ensure_config_dir`).
    """
    subprocess.check_call(["navsyncdb", "-c", "--drop-database"])
    _load_test_data()
    _set_admin_password()


# --- helpers ----------------------------------------------------------------


def _get_test_database_name() -> str:
    name = os.environ.get("PGDATABASE", "nav_test")
    print(f"Using {name} as NAV test database for this test session")
    return name


def _write_db_conf(config_dir: Path) -> None:
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    user = os.environ.get("PGUSER", "nav")
    password = os.environ.get("PGPASSWORD", "")
    dbname = _get_test_database_name()

    db_conf = config_dir / "db.conf"
    db_conf.write_text(
        f"dbhost={host}\n"
        f"dbport={port}\n"
        f"db_nav={dbname}\n"
        f"script_default={user}\n"
        f"userpw_{user}={password}\n"
    )


def _patch_nav_conf(config_dir: Path) -> None:
    nav_conf = config_dir / "nav.conf"
    text = nav_conf.read_text()

    upload_dir = config_dir / "uploads"
    upload_dir.mkdir(exist_ok=True)

    replacements = {
        "NAV_USER=navcron": f"NAV_USER={getpass.getuser()}",
        "#DJANGO_DEBUG=True": "DJANGO_DEBUG=True",
        "#UPLOAD_DIR=/usr/share/nav/var/uploads": f"UPLOAD_DIR={upload_dir}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    nav_conf.write_text(text)


def _patch_graphite_conf(config_dir: Path) -> None:
    graphite_conf = config_dir / "graphite.conf"
    text = graphite_conf.read_text()
    text = text.replace(
        "#base=http://localhost:8000/",
        "base=http://localhost:9000",
    )
    graphite_conf.write_text(text)


def _refresh_nav_config() -> None:
    """Re-read nav.conf into the already-imported NAV_CONFIG dict."""
    from nav.config import NAV_CONFIG, read_flat_config

    NAV_CONFIG.update(read_flat_config("nav.conf"))


def _load_test_data() -> None:
    test_data = Path(__file__).resolve().parent / "test-data.sql"
    dbname = _get_test_database_name()
    subprocess.check_call(["psql", "-f", str(test_data), dbname])


def _set_admin_password() -> None:
    dbname = _get_test_database_name()
    subprocess.check_call(
        [
            "psql",
            "-c",
            f"UPDATE account SET password = '{ADMIN_PASSWORD}' WHERE login = 'admin'",
            dbname,
        ]
    )
