"""NAV build configuration variables."""
# pylint: disable=invalid-name
import os
import getpass
import pkg_resources
import sysconfig

datadir = os.path.join(sysconfig.get_config_var('datarootdir'), 'nav')
sysconfdir = os.path.join(datadir, 'conf')
localstatedir = os.path.join(datadir, 'var')
webrootdir = os.path.join(datadir, "www")
crondir = os.path.join(sysconfdir, "cron.d")
djangotmpldir = os.path.join(datadir, "templates")
docdir = os.path.join(datadir, "doc")
nav_user = (getpass.getuser() if os.geteuid() != 0
            else os.getenv("NAV_USER", "navcron"))
VERSION = pkg_resources.get_distribution("nav").version
