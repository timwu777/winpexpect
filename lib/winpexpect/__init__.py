#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

__all__ = ['spawn', 'Process', 'Terminal', 'NBIO', 'Searcher',
           'EOF', 'TIMEOUT']

import sys

from winpexpect.exception import *
from winpexpect.search import Searcher

if sys.platform in ('linux2', 'darwin'):
    from winpexpect.posix import (PosixProcess as Process,
            PosixTerminal as Terminal, PosixNBIO as NBIO)

else:
    raise RuntimeError('This platform is not supported')

try:
    import gevent
except ImportError:
    pass
else:
    from winpexpect.gevent import GEventNBIO
    __all__.append('GEventNBIO')


default_process_class = Process
default_terminal_class = Terminal
default_nbio_class = NBIO


def spawn(command, args=[], cwd=None, env=None, timeout=30,
          maxread=200, searchwindowsize=None, ignorecase=False,
          process_class=None, terminal_class=None, nbio_class=None):
    """Spawn a command and return a `Spawn` instance."""
    if process_class is None:
        process_class = default_process_class
    if terminal_class is None:
        terminal_class = default_terminal_class
    if nbio_class is None:
        nbio_class = default_nbio_class
    def __init__(self):
        process_class.__init__(self, command, args, cwd, env)
        process_class.start(self)
        fd = process_class.fileno(self)
        terminal_class.__init__(self, fd)
        nbio_class.__init__(self, fd, timeout)
        Searcher.__init__(self, fd, maxread, searchwindowsize, ignorecase)
        self.expect = self.search
        self.send = self.write
    cls = type('Spawn', (nbio_class, process_class, terminal_class, Searcher),
               { '__init__': __init__ })
    return cls()
