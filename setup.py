from glob import glob
from setuptools import setup
from setuptools.command.build import build


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
    sass_manifests={
        'nav.web': {
            'sass_path': 'sass',
            'css_path': 'static/css',
            'strip_extension': True,
        },
    },
)
