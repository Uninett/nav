import os
import subprocess
from glob import glob
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

TOP_SRCDIR = os.path.abspath(os.path.dirname(__file__))


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def find_scripts():
    for candidate in glob('bin/*'):
        with open(candidate) as handle:
            if handle.readline().startswith("#!"):
                yield candidate


class Build(build_py):
    def run(self):
        # customized build commmand
        if not self.dry_run:
            if not os.path.exists("nav/buildconf.py"):
                print("HOLY MACKEREL, BATMAN, NO BUILDCONF EXISTS YET")

        build_py.run(self)


setup(
    setup_requires=['libsass >= 0.6.0', 'setuptools_scm'],
    python_requires=">=2.7",
    use_scm_version=True,

    name="nav",
    author="Uninett AS",
    author_email="nav-support@uninett.no",
    description=("Network Administration Visualized - A comprehensive, free "
                 "Network Management System"),
    license="GPLv2",
    keywords="nms snmp",
    url="https://nav.uninett.no/",
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 6 - Mature",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],

    cmdclass={
        'build_py': Build,
    },

    scripts=list(find_scripts()),
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['static', 'sql', 'templates'],
    },

    sass_manifests={
        'nav': (os.path.join(TOP_SRCDIR, 'nav/web/sass'),
                os.path.join(TOP_SRCDIR, 'nav/web/static/css')),
    },

    zip_safe=False,
)
