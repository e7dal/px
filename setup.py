#!/usr/bin/env python

import os
import re
import filecmp
import tempfile
import subprocess

from setuptools import setup

VERSIONFILE = 'px/version.py'

git_version = subprocess.check_output(['git', 'describe', '--dirty']).decode('utf-8').strip()
with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tmp:
    tmp.write(b"# NOTE: Auto generated by setup.py, no touchie!\n")
    tmp.write(b"VERSION = '%s'\n" % bytearray(git_version, "utf_8"))

    # Flushing is required for filecmp.cmp() to work (below)
    tmp.flush()

    if not os.path.isfile(VERSIONFILE):
        # No version file found
        os.rename(tmp.name, VERSIONFILE)
    elif not filecmp.cmp(tmp.name, VERSIONFILE):
        # Version file needs updating
        os.rename(tmp.name, VERSIONFILE)
    else:
        # VERSIONFILE was already up to date. If we touch it in this
        # case, it will have its file timestamp updated, which will
        # force the slow px_integration_test.py tests to get rerun.
        #
        # Just clean up our tempfile and be merry.
        os.remove(tmp.name)

requirements = None
with open('requirements.txt') as reqsfile:
    requirements = reqsfile.readlines()

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as fp:
    LONG_DESCRIPTION = fp.read()

if not re.match(r'^[0-9]+\.[0-9]+\.[0-9]+$', git_version):
    # Setuptools wants nice version numbers
    git_version = "0.0.0"

setup(
    name='pxpx',
    version=git_version,
    description='ps and top for Human Beings',
    long_description=LONG_DESCRIPTION,
    author='Johan Walles',
    author_email='johan.walles@gmail.com',
    url='https://github.com/walles/px',
    license='MIT',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ],

    packages=['px'],

    install_requires=requirements,

    # See: http://setuptools.readthedocs.io/en/latest/setuptools.html#setting-the-zip-safe-flag
    zip_safe=True,

    entry_points={
        'console_scripts': [
            'px = px.px:main',
            'ptop = px.px:main'
        ],
    }

    # Note that we're by design *not* installing man pages here.
    # Using "data_files=" only puts the man pages in the egg file,
    # and installing that egg doesn't put them on the destination
    # system.
    #
    # After trying to figure this out for a bit, my conclusion is
    # that "pip install" simply isn't meant for installing any man
    # pages.
    #
    #   /johan.walles@gmail.com 2018aug27
)
