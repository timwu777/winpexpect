#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.


class Process(object):
    """A file-like interface to a process.

    This class does not provide any implementations itself but defines
    the interface that is implemented by platform-specific subclasses.
    """

    def __init__(self, command, args=[], cwd=None, env=None):
        """Constructor."""

    def fileno(self):
        """Return the file descriptor that is attached to the terminal."""

    def read(self, size=None):
        """Read from the process."""

    def write(self, buf):
        """Write to the process."""

    def close(self):
        """Close the communictions channel with the process. This will
        terminate the process."""

    def start(self):
        """Start the process."""

    def terminate(self, timeout):
        """Terminate the process."""

    def kill(self, signal):
        """Send a signal to the child process."""

    def wait(self, timeout=None):
        """Wait until the process exits."""

    def isalive(self):
        """Return whether or not the process is alive."""
