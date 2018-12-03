import os
import subprocess
from glob import glob
from setuptools import setup, find_packages
from distutils.command.build import build

TOP_SRCDIR = os.path.abspath(os.path.dirname(__file__))


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


# Ensure CSS files are built every time build is invoked
build.sub_commands = [('build_sass', None)] + build.sub_commands


setup(
    setup_requires=['libsass', 'setuptools_scm'],
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

    scripts=list(find_scripts()),
    package_dir={'': 'python'},
    packages=find_packages('python'),
    include_package_data=True,
    package_data={
        '': ['static', 'sql', 'templates', 'etc'],
    },
    data_files=etc_files(),

    sass_manifests={
        'nav.web': {
            'sass_path': 'sass',
            'css_path': 'static/css',
            'strip_extension': True,
        },
    },

    zip_safe=False,
    install_requires=[
        'Django==1.7.1',
        'django-hstore>=1.2.4,<1.3',
        'django-filter>=0.7,<0.12',
        'django-crispy-forms>=1.5,<1.6',
        'crispy-forms-foundation==0.5.4',
        'djangorestframework>=3.3,<3.4',
        'asciitree==0.3.3',
        'configparser==3.5.0',
        'psycopg2==2.5.4',
        'IPy==0.83',
        'pyaml',
        'twisted>=14.0.1,<18',
        'networkx>=1.7,<1.8',
        'xmpppy==0.5.0rc1',
        'Pillow==3.0.0',
        'pyrad==2.1',
        'python-ldap==3.0.0',
        'sphinx>=1.0',
        'feedparser>=5.1.2,<5.2',
        'markdown==2.5.1',
        'dnspython==1.15.0',
        'iso8601',
        'pynetsnmp-2==0.1.3',
        'libsass==0.15.1',
    ],
)
