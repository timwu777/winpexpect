#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

from __future__ import absolute_import

from gevent import fd, Timeout

from winpexpect import compat
from winpexpect.nbio import NBIO
from winpexpect.exception import TIMEOUT


class GEventNBIO(NBIO):
    """Non-blocking IO support for gevent.

    This will make winpexect cooperate with gevent.
    """

    def __init__(self, fd, timeout=None):
        self.fd = fd
        self.timeout = timeout

    def settimeout(self, timeout):
        self.timeout = timeout

    def read(self, nbytes):
        if self.timeout is None:
            timeout = None
        else:
            timeout = Timeout(self.timeout)
            timeout.start()
        try:
            buf = fd.read(self.fd, nbytes)
        except Timeout as e:
            if e is not timeout:
                raise
            raise TIMEOUT('Timeout reading from fd')
        else:
            if timeout is not None:
                timeout.cancel()
        return buf

    def write(self, buf):
        if self.timeout is None:
            timeout = None
        else:
            timeout = Timeout(self.timeout)
            timeout.start()
        buf = compat.buffer(buf)
        byteswritten = 0
        try:
            while byteswritten != len(buf):
                nbytes = fd.write(self.fd, buf[byteswritten:])
                assert nbytes != 0
                byteswritten += nbytes
        except Timeout as e:
            if e is not timeout:
                raise
            raise TIMEOUT('Timeout writing to fd')
        else:
            if timeout is not None:
                timeout.cancel()
        return len(buf)
