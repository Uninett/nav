import os
from glob import glob
from setuptools import setup, find_packages
from distutils.command.build import build

TOP_SRCDIR = os.path.abspath(os.path.dirname(__file__))


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def etc_files():
    return [
        (d, [os.path.join(d, f) for f in files]) for d, folders, files in os.walk('etc')
    ]


def find_scripts():
    for candidate in glob('bin/*'):
        with open(candidate) as handle:
            if handle.readline().startswith("#!"):
                yield candidate


# Ensure CSS files are built every time build is invoked
build.sub_commands = [('build_sass', None)] + build.sub_commands


setup(
    setup_requires=['libsass', 'setuptools_scm'],
    python_requires=">=3.7",
    use_scm_version=True,
    name="nav",
    author="Uninett AS",
    author_email="nav-support@uninett.no",
    description=(
        "Network Administration Visualized - A comprehensive, free "
        "Network Management System"
    ),
    license="GPLv3",
    keywords="nms snmp",
    url="https://nav.uninett.no/",
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 6 - Mature",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    scripts=list(find_scripts()),
    package_dir={'': 'python'},
    packages=find_packages('python'),
    include_package_data=True,
    package_data={'': ['static', 'sql', 'templates', 'etc'],},
    data_files=etc_files(),
    sass_manifests={
        'nav.web': {
            'sass_path': 'sass',
            'css_path': 'static/css',
            'strip_extension': True,
        },
    },
    zip_safe=False,
)
