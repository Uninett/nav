"""Configure the virtualenv for local NAV development.

Writes sitecustomize.py (env defaults), installs NAV config templates,
and patches them for local Docker services.

Run via: uv run python tools/local-dev/configure.py
"""

import getpass
import os
import site
import subprocess
import sys
from pathlib import Path
from string import Template

SCRIPT_DIR = Path(__file__).parent
VENV_DIR = Path(sys.prefix)
SITE_PACKAGES = Path(site.getsitepackages()[0])
NAV_CONFIG_DIR = VENV_DIR / "etc" / "nav"
PG_PORT = os.environ.get("NAV_PG_PORT", "5434")

DB_CONF = Template("""\
dbhost=127.0.0.1
dbport=$pg_port
db_nav=nav
script_default=nav
userpw_nav=nav
""")

GRAPHITE_CONF = """\
[carbon]
host=localhost
port=2003

[graphiteweb]
base=http://localhost:8088/
"""


def info(msg):
    print(f"\033[0;32m==>\033[0m {msg}")


def write_sitecustomize():
    template = Template((SCRIPT_DIR / "sitecustomize.py.tmpl").read_text())
    dest = SITE_PACKAGES / "sitecustomize.py"
    info(f"Writing {dest}")
    dest.write_text(template.substitute(pg_port=PG_PORT))


def install_nav_config():
    info(f"Installing NAV config templates to {NAV_CONFIG_DIR}")
    subprocess.run(
        ["nav", "config", "install", str(NAV_CONFIG_DIR)],
        capture_output=True,
    )


def write_db_conf():
    path = NAV_CONFIG_DIR / "db.conf"
    info(f"Writing {path}")
    path.write_text(DB_CONF.substitute(pg_port=PG_PORT))


def write_nav_conf():
    path = NAV_CONFIG_DIR / "nav.conf"
    upload_dir = VENV_DIR / "var" / "nav" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    info(f"Configuring {path}")
    # nav.conf is parsed by read_flat_config() which uses last-value-wins,
    # so we can just append our overrides.
    with path.open("a") as f:
        f.write("\n# Local dev overrides\n")
        f.write(f"NAV_USER={getpass.getuser()}\n")
        f.write("DJANGO_DEBUG=True\n")
        f.write(f"UPLOAD_DIR={upload_dir}\n")


def write_graphite_conf():
    path = NAV_CONFIG_DIR / "graphite.conf"
    info(f"Writing {path}")
    path.write_text(GRAPHITE_CONF)


def main():
    info(f"Virtualenv: {VENV_DIR}")
    info(f"NAV config: {NAV_CONFIG_DIR}")
    write_sitecustomize()
    install_nav_config()
    write_db_conf()
    write_nav_conf()
    write_graphite_conf()


if __name__ == "__main__":
    main()
