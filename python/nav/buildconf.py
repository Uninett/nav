"""NAV build configuration variables."""
# pylint: disable=invalid-name
import os
import sysconfig

try:
    from importlib import metadata as _impmeta
except ImportError:
    import importlib_metadata as _impmeta


datadir = os.path.join(sysconfig.get_config_var('datarootdir'), 'nav')
localstatedir = os.path.join(datadir, 'var')
webrootdir = os.path.join(datadir, "www")
djangotmpldir = os.path.join(datadir, "templates")
docdir = os.path.join(datadir, "doc")


try:
    VERSION = _impmeta.version("nav")
except _impmeta.PackageNotFoundError:
    # If we're not installed, try to get the current version from Git tags
    import setuptools_scm

    VERSION = setuptools_scm.get_version()
