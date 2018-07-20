import os
from glob import glob
from setuptools import setup, find_packages
from distutils.command.build import build


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def etc_files():
    return [(d, [os.path.join(d,f) for f in files])
            for d, folders, files in os.walk('etc')]


def find_scripts():
    for candidate in glob('bin/*'):
        with open(candidate) as handle:
            if handle.readline().startswith("#!"):
                yield candidate


class NAVBuild(build):
    sub_commands = [
        ('build_sass', None),
    ] + build.sub_commands


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
        'build': NAVBuild,
    },

    scripts=list(find_scripts()),
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['static', 'sql', 'templates'],
    },
    exclude_package_data={
        'nav.web': ['*.scss'],  # no need to install source SASS files
    },
    data_files=etc_files(),

    sass_manifests={
        'nav': ('web/sass',
                'web/static/css'),
    },

    zip_safe=False,
)
