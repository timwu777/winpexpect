#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import os

import winpexpect
from winpexpect import *
from winpexpect.test import *


class TestSpawnPosix(PosixTest):

    def test_spawn(self):
        env = { 'PS1': '$', 'HOME': os.getcwd() }
        shell = spawn('/bin/sh', env=env, timeout=2)
        shell.expect('\\$')
        shell.send('uname\n')
        # The shell echos 'uname\r\n'
        shell.expect('\r\n')
        shell.expect('\r\n')
        uname = shell.before
        assert uname == os.uname()[0]

    def test_spawn_gevent(self):
        if not hasattr(winpexpect, 'GEventNBIO'):
            raise SkipTest('This test requires gevent to be installed')
        env = { 'PS1': '$', 'HOME': os.getcwd() }
        shell = spawn('/bin/sh', env=env, timeout=2, nbio_class=GEventNBIO)
        shell.expect('\\$')
        shell.send('uname\n')
        # The shell echos 'uname\r\n'
        shell.expect('\r\n')
        shell.expect('\r\n')
        uname = shell.before
        assert uname == os.uname()[0]
