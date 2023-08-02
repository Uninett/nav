import os
from glob import glob
from setuptools import setup, find_packages
from distutils.command.build import build


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
    scripts=list(find_scripts()),
    package_dir={'': 'python'},
    packages=find_packages('python'),
    package_data={'': ['static', 'sql', 'templates', 'etc']},
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
