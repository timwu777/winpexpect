#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

from setuptools import setup

setup(
    name = 'winpexpect',
    version = '2.0a3',
    description = 'A version of pexpect that works on Unix and Windows.',
    author = 'Geert Jansen',
    author_email = 'geertj@gmail.com',
    url = 'http://github.com/geertj/winpexpect',
    license = 'MIT',
    classifiers = ['Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Operating System :: Microsoft :: Posix',
        'Operating System :: Microsoft :: Windows'],
    package_dir = {'': 'lib'},
    packages = ['winpexpect', 'winpexpect.test'],
    test_suite = 'nose.collector'
)
