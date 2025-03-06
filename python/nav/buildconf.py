"""NAV build configuration variables."""

from importlib import metadata
import os
import sysconfig


datadir = os.path.join(sysconfig.get_config_var('datarootdir'), 'nav')
localstatedir = os.path.join(datadir, 'var')
webrootdir = os.path.join(datadir, "www")
djangotmpldir = os.path.join(datadir, "templates")
docdir = os.path.join(datadir, "doc")


try:
    VERSION = metadata.version("nav")
except metadata.PackageNotFoundError:
    # If we're not installed, try to get the current version from Git tags
    import setuptools_scm

    VERSION = setuptools_scm.get_version()
