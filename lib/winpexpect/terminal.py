#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.


class Terminal(object):
    """Terminal control.

    This class does not provide any implementations itself but defines
    the interface that is implemented by platform specific subclasses.
    """

    def __init__(self, fd=None):
        """Constructor.
        
        If the `fd` argument is provided, it must be a file descriptor of
        the current process' controlling terminal. If `fd` is not provided,
        the controlling terminal is determined using `ttyname()`.

        It is an error if `fd` does not correspond to a terminal or if the
        current process has no controlling terminal.
        """

    def clear(self):
        """Clear the screen."""

    def getecho(self):
        """Return the echo mode."""

    def setecho(self, echo):
        """Set the echo mode."""

    def getwinsize(self):
        """Return the window size as a tuple (rows, cols)."""

    def setwinsize(self, rows, cols):
        """Set the window size."""
