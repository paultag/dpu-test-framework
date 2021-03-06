#!/usr/bin/env python

from dpu import __appname__, __version__
from setuptools import setup

long_description = open('README.md').read()

setup(
    name=__appname__,
    version=__version__,
    packages=['dpu'],
    author="DPU Authors",
    author_email="tag@pault.ag",
    long_description=long_description,
    description='Debian Package Utility test framework',
    license="GPL-2+",
    url="",
    platforms=['any']
)
