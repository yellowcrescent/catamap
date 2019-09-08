#!/usr/bin/env python3
# pylint: disable=W,C

from setuptools import setup, find_packages
setup(
    name = "catamap",
    version = "0.1.0",
    author = "Jacob Hipps",
    author_email = "jacob@ycnrg.org",
    license = "GPLv3",
    description = "Cataclysm DDA map rendering tools",
    keywords = "cataclysm game tools overviewer map render parser",
    url = "https://git.ycnrg.org/projects/GTOOL/repos/catamap",

    packages = find_packages(),
    scripts = [],

    install_requires = ['arrow', 'requests'],

    package_data = {
        '': [ '*.md' ],
    },

    entry_points = {
        'console_scripts': [ 'catamap = catamap.cli:_main' ]
    }

    # could also include long_description, download_url, classifiers, etc.
)
