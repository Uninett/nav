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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Manage vendored JS libraries via npm."""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBS = ROOT / "python/nav/web/static/js/libs"
CONFIG = ROOT / "python/nav/web/static/js/require_config.js"
NODE = ROOT / "node_modules"
VERSION_RE = re.compile(r"-(\d+\.\d+[\d.a-zA-Z-]*?)(\.min)?\.js$")

# Packages whose dist file can't be resolved automatically from
# package.json fields (jsdelivr, unpkg, browser, main).
# Map npm name to the dist path relative to the package in node_modules.
OVERRIDES = {
    "driver.js": "dist/driver.js.iife.min.js",
    "jquery-ui": "dist/jquery-ui.min.js",
    "requirejs": "require.js",
}


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def get_deps():
    return _load_json(ROOT / "package.json").get("dependencies", {})


def _minified_variants(path):
    """Return .min.js and -min.js variants of a .js path."""
    if path.endswith(".min.js"):
        return ()
    base = path.removesuffix(".js")
    return (base + ".min.js", base + "-min.js")


def _resolve_from_override(npm_name):
    """Check OVERRIDES for a manually specified dist path.

    Returns the path string if the override exists on disk, or None.
    """
    path = OVERRIDES.get(npm_name)
    if path and (NODE / npm_name / path).exists():
        return path
    return None


def _resolve_from_package(npm_name, pkg):
    """Find the dist file by inspecting package.json fields.

    Checks jsdelivr, unpkg, browser, and main fields in order, preferring
    minified variants. Returns the path string, or None.
    """
    for field in ("jsdelivr", "unpkg", "browser", "main"):
        path = pkg.get(field)
        if not isinstance(path, str) or not path.endswith(".js"):
            continue
        for min_path in _minified_variants(path):
            if (NODE / npm_name / min_path).exists():
                return min_path
        if (NODE / npm_name / path).exists():
            return path
    return None


def resolve_source(npm_name):
    """Find the .min.js dist file and version for a package in node_modules.

    Returns (source_path, version) or (None, None).
    """
    pkg_path = NODE / npm_name / "package.json"
    if not pkg_path.exists():
        return None, None
    pkg = _load_json(pkg_path)
    version = pkg.get("version")
    source = _resolve_from_override(npm_name) or _resolve_from_package(npm_name, pkg)
    return source, version


GENERIC_STEMS = {"cdn", "index", "dist", "main", "umd", "bundle"}

_STRIP_SUFFIXES = (".min", "-min", ".iife", ".esm", ".cjs", ".umd", ".js")


def _derive_name(npm_name, source_path):
    """Derive a short library name from the dist file, or fall back to npm name.

    'dist/jquery.min.js'          -> 'jquery'
    'dist/driver.js.iife.min.js'  -> 'driver'
    'cdn.min.js'                  -> falls back to npm_name
    """
    stem = Path(source_path).stem
    for suffix in _STRIP_SUFFIXES:
        stem = stem.removesuffix(suffix)
    stem = stem.lower()
    if stem in GENERIC_STEMS:
        return npm_name
    return stem


def local_name(npm_name, source_path, version):
    """'jquery', 'dist/jquery.min.js', '4.0.0' -> 'jquery-4.0.0.min.js'"""
    return f"{_derive_name(npm_name, source_path)}-{version}.min.js"


def find_old_file(base):
    """Find existing file in libs/ matching a base name."""
    for f in LIBS.glob("*.js"):
        m = VERSION_RE.search(f.name)
        if m and f.name[: m.start()].lower() == base:
            return f.name
    return None


def sync_one(npm_name, config_text=None):
    """Sync one package. Returns (old, new, updated_config_text) or None.

    If config_text is provided, references are updated in-memory and the
    modified text is returned so the caller can batch-write once.
    """
    source, version = resolve_source(npm_name)
    if not source:
        return None

    name = _derive_name(npm_name, source)
    new = local_name(npm_name, source, version)
    if (LIBS / new).exists():
        return None

    old = find_old_file(name)

    shutil.copy2(NODE / npm_name / source, LIBS / new)

    if old and old != new:
        (LIBS / old).unlink(missing_ok=True)
        old_ref = f"libs/{old.removesuffix('.js')}"
        new_ref = f"libs/{new.removesuffix('.js')}"
        if config_text is None:
            config_text = CONFIG.read_text()
        config_text = config_text.replace(old_ref, new_ref)

    return old, new, config_text


def npm_install(*args):
    r = subprocess.run(
        ["npm", "install", "--legacy-peer-deps", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        sys.exit(f"npm install failed:\n{r.stderr}")


def _check_node_modules():
    if not NODE.exists():
        print("Note: node_modules not found. Run 'npm install --legacy-peer-deps'")
        print("      to enable version resolution from installed packages.\n")
        return False
    return True


def cmd_list():
    _check_node_modules()
    managed_files = set()
    unresolved = []
    rows = []
    for npm_name, version in sorted(get_deps().items()):
        source, _ = resolve_source(npm_name)
        path = source or OVERRIDES.get(npm_name)
        name = _derive_name(npm_name, path) if path else npm_name
        local = find_old_file(name)
        if local:
            managed_files.add(local)
        else:
            unresolved.append(npm_name)
        rows.append((npm_name, version, local or "(not synced)"))
    for f in sorted(LIBS.glob("*.js")):
        if f.name not in managed_files and VERSION_RE.search(f.name):
            rows.append(("(untracked)", "", f.name))
    if not rows:
        print("No vendored libraries")
        return
    w0 = max(len(r[0]) for r in rows + [("Name",)])
    w1 = max(len(r[1]) for r in rows + [("", "Version")])
    print(f"  {'Name':<{w0}}  {'Version':<{w1}}  File")
    print(f"  {'-' * w0}  {'-' * w1}  {'-' * max(len(r[2]) for r in rows)}")
    for name, version, local in rows:
        print(f"  {name:<{w0}}  {version:<{w1}}  {local}")
    if unresolved:
        print(f"\nHint: {len(unresolved)} package(s) not synced. Run 'sync' or add")
        print("an entry to OVERRIDES in tools/vendor.py if auto-resolution fails.")


def cmd_check():
    """Check for version mismatches, missing files, and untracked vendors."""
    _check_node_modules()
    problems = []
    managed_files = set()

    for npm_name, version in sorted(get_deps().items()):
        source, _ = resolve_source(npm_name)
        if not source:
            problems.append(f"  {npm_name}: cannot resolve dist file")
            continue
        name = _derive_name(npm_name, source)
        expected = local_name(npm_name, source, version)
        actual = find_old_file(name)
        if actual:
            managed_files.add(actual)
        if not actual:
            problems.append(f"  {npm_name}: not synced (expected {expected})")
        elif actual != expected:
            problems.append(f"  {npm_name}: version mismatch ({actual} != {expected})")

    for f in sorted(LIBS.glob("*.js")):
        if f.name not in managed_files and VERSION_RE.search(f.name):
            problems.append(f"  {f.name}: untracked")

    if problems:
        print("Problems found:")
        for p in problems:
            print(p)
        sys.exit(1)
    else:
        print("All vendored libraries OK")


def cmd_sync():
    if not NODE.exists():
        print("node_modules not found, running npm install...")
        npm_install()
    original_config = CONFIG.read_text()
    config_text = original_config
    n = 0
    for pkg in sorted(get_deps()):
        result = sync_one(pkg, config_text)
        if result:
            old, new, config_text = result
            print(f"  {pkg}: {old or '(new)'} -> {new}")
            n += 1
    if config_text != original_config:
        CONFIG.write_text(config_text)
    print(f"\nSynced {n} library(ies)" if n else "Everything up to date")


def _install_and_sync(name, version=None):
    """Install a package via npm and sync the vendored file.

    Returns (old, new) on success, or None.
    """
    spec = f"{name}@{version}" if version else f"{name}@latest"
    npm_install("--save-exact", spec)
    result = sync_one(name)
    if not result:
        return None
    old, new, config_text = result
    if config_text is not None:
        CONFIG.write_text(config_text)
    return old, new


def cmd_update(name, version=None):
    result = _install_and_sync(name, version)
    if result:
        old, new = result
        print(f"Updated: {old} -> {new}")
    else:
        print(f"{name} already up to date")


def cmd_add(name, version=None):
    result = _install_and_sync(name, version)
    if result:
        _, new = result
        alias = VERSION_RE.sub("", new).removesuffix(".min.js")
        ref = new.removesuffix(".js")
        print(f"Added: {new}")
        print(f'Add to require_config.js: "{alias}": "libs/{ref}",')
    else:
        print("Could not resolve dist file automatically.")
        print("Add an entry to OVERRIDES in tools/vendor.py and re-run.")


def cmd_remove(npm_name):
    source, _ = resolve_source(npm_name)
    if source:
        old = find_old_file(_derive_name(npm_name, source))
        if old:
            (LIBS / old).unlink()
            print(f"Removed: {old}")
            old_ref = f"libs/{old.removesuffix('.js')}"
            config_text = CONFIG.read_text()
            lines = config_text.splitlines(keepends=True)
            new_lines = [line for line in lines if old_ref not in line]
            if len(new_lines) < len(lines):
                CONFIG.write_text("".join(new_lines))
                print("Removed entry from require_config.js")
    else:
        print(f"Could not resolve dist file for {npm_name}, skipping file cleanup")
    r = subprocess.run(["npm", "uninstall", npm_name], cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"npm uninstall failed for {npm_name}")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List vendored libraries and their status")
    sub.add_parser("check", help="Check for version mismatches and untracked files")
    sub.add_parser("sync", help="Sync all vendored libraries from node_modules")

    update = sub.add_parser("update", help="Update a vendored package")
    update.add_argument("pkg", help="npm package name")
    update.add_argument("--version", dest="version", help="Target version")

    add = sub.add_parser("add", help="Add a new vendored package")
    add.add_argument("pkg", help="npm package name")
    add.add_argument("--version", dest="version", help="Target version")

    remove = sub.add_parser("remove", help="Remove a vendored package")
    remove.add_argument("pkg", help="npm package name")

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list":
        cmd_list()
    elif args.command == "check":
        cmd_check()
    elif args.command == "sync":
        cmd_sync()
    elif args.command == "update":
        cmd_update(args.pkg, args.version)
    elif args.command == "add":
        cmd_add(args.pkg, args.version)
    elif args.command == "remove":
        cmd_remove(args.pkg)
