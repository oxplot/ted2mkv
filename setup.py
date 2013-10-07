#!/usr/bin/env python

from distutils.core import setup
import ted2mkv

setup(
  name = 'ted2mkv',
  version = ted2mkv.__version__,
  packages = ['ted2mkv'],
  scripts = ['scripts/ted2mkv', 'scripts/ted-listall'],

  author = 'Mansour Behabadi',
  author_email = 'mansour@oxplot.com',
  maintainer = 'Mansour Behabadi',
  maintainer_email = 'mansour@oxplot.com',
  description = 'Download and convert TED videos to MKV format',
  long_description = open('README', 'r').read(),
  license = 'GPLv3',
  url = 'https://github.com/oxplot/ted2mkv',

  classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Topic :: Multimedia :: Video :: Conversion',
    'Topic :: Utilities'
  ]
)
