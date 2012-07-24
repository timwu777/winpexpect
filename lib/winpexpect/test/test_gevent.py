#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import os
import time
import select

import gevent
from nose import SkipTest
from winpexpect.test import *

try:
    from winpexpect.gevent import *
except ImportError:
    raise
    GEventNBIO = None


class TestGEventNBIO(UnitTest):

    @classmethod
    def setup_class(cls):
        if GEventNBIO is None:
            raise SkipTest('gevent must be installed to run this test')
        super(TestGEventNBIO, cls).setup_class()

    def test_read(self):
        r, w = os.pipe()
        io = GEventNBIO(r)
        io.settimeout(0)
        start = time.time()
        assert_raises(TIMEOUT, io.read, 1)
        end = time.time()
        assert end - start < 1.0
        io.settimeout(1.0)
        start = time.time()
        assert_raises(TIMEOUT, io.read, 1)
        end = time.time()
        assert end - start > 1.0

    def test_write(self):
        r, w = os.pipe()
        io = GEventNBIO(w)
        io.settimeout(0)
        buf = 1000 * select.PIPE_BUF * b'x'
        start = time.time()
        assert_raises(TIMEOUT, io.write, buf)
        end = time.time()
        assert end - start < 1.0
        buf2 = os.read(r, select.PIPE_BUF)
        assert len(buf2) == select.PIPE_BUF
        io.settimeout(1.0)
        start = time.time()
        assert_raises(TIMEOUT, io.write, buf)
        end = time.time()
        assert end - start > 1.0

    def test_continue_short_write(self):
        r, w = os.pipe()
        nbytes = 1000 * select.PIPE_BUF
        buf = nbytes * b'x'
        rio = GEventNBIO(r)
        wio = GEventNBIO(w)
        wio.settimeout(2)
        bytesread = [0]  # lack of "nonlocal" in 2.x
        def consume():
            gevent.sleep(1)
            while True:
                bytesread[0] += len(rio.read(select.PIPE_BUF))
                if bytesread[0] == nbytes:
                    break
        consumer = gevent.Greenlet(consume)
        consumer.start()
        byteswritten = wio.write(buf)
        consumer.join()
        assert bytesread[0] == nbytes
        assert byteswritten == nbytes
