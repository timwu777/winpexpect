#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

from winpexpect.exception import TIMEOUT


class NBIO(object):
    """Non-blocking IO."""

    def __init__(self, fd):
        """Constructor."""

    def settimeout(self, timeout):
        """Set the timeout for this file descriptor.

        The `timeout` parameter an be a float, or None. If it is a float, it
        specifies the timeout in seconds to use. A value of 0.0 for the timeout
        never waits and will perform regular non-blocking I/O. A value of
        `None` for the timeout corresponds to an infinite timeout and will
        perform regular blocking I/O.
        """

    def read(self, size):
        """Read up to `size` bytes form the file descriptor.

        The return value is the string that was read. In case no data could
        be read before a timeout occurred, the TIMEOUT exception is raised.

        This method will return as soon as data is available, even if the data
        available is less than `size`.
        """

    def write(self, buf):
        """Write `buf` to the file descriptor.

        This will retry short writes up to the timeout.
        """
