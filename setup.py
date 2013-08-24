#!/usr/bin/env python

from setuptools import setup, find_packages

try:
    README = open('README.rst').read()
except:
    README = None

try:
    REQUIREMENTS = open('requirements.txt').read()
except:
    REQUIREMENTS = None

setup(
    name='spotify2piratebay',
    version="0.1",
    description='Download your Spotify music using the Pirate Bay',
    long_description=README,
    install_requires=REQUIREMENTS,
    author='Mathijs de Bruin',
    author_email='mathijs@visualspace.nl',
    url='http://github.com/dokterbob/spotify2piratebay/',
    packages=find_packages(),
    include_package_data=True,
    classifiers=['Development Status :: 3 - Alpha',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: Public Domain',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Utilities'],
    # entry_points={
    #     'console_scripts': [
    #         'spotify2piratebay = spotify2piratebay.runner:main',
    #     ],
    # },
)
