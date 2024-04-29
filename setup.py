from glob import glob
from setuptools import setup
from setuptools.command.build import build


# Ensure CSS files are built every time build is invoked
build.sub_commands = [('build_sass', None)] + build.sub_commands


setup(
    setup_requires=['libsass', 'setuptools_scm'],
    sass_manifests={
        'nav.web': {
            'sass_path': 'sass',
            'css_path': 'static/css',
            'strip_extension': True,
        },
    },
)
