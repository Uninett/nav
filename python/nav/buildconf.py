"""NAV build configuration variables."""
# pylint: disable=invalid-name
import os
import sysconfig
import pkg_resources

datadir = os.path.join(sysconfig.get_config_var('datarootdir'), 'nav')
localstatedir = os.path.join(datadir, 'var')
webrootdir = os.path.join(datadir, "www")
djangotmpldir = os.path.join(datadir, "templates")
docdir = os.path.join(datadir, "doc")

try:
    VERSION = pkg_resources.get_distribution("nav").version
except pkg_resources.DistributionNotFound:
    # If we're not installed, try to get the current version from Git tags
    import setuptools_scm
    VERSION = setuptools_scm.get_version()
