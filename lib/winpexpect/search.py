#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import os
import re

from winpexpect import compat
from winpexpect.exception import EOF


class Searcher(object):
    """Searcher.

    This class passes over an input stream matching patterns.
    """

    def __init__(self, stream, maxread=2000, searchwindowsize=None,
                 ignorecase=False):
        """Constructor.
        
        The `stream` argument must be a file descriptor, a file objects
        or a socket.

        The `maxread`, `searchwindowsize` and `ignorecase` parameters tune
        the matching algorithm. Maxread specifies the characters to read at
        a time. The search window determines the amount of characters at the
        end of the current position to look for a match. And if ignorecase
        is set, a case insensitive match is used.
        """
        self.stream = stream
        self.maxread = maxread
        self.searchwindowsize = searchwindowsize
        self.ignorecase = ignorecase
        self.buffer = ''

    def read(self, size):
        """Read up to `size` bytes form the input.

        This class expects blocking behavior from the read, i.e.  this
        should block until at least one character is available, or until
        an end-of-file is reached.
        """
        stream = self.stream
        if isinstance(stream, int):
            return os.read(stream, size)
        elif hasattr(stream, 'read'):
            return stream.read(size)
        elif hasattr(stream, 'recv'):
            return stream.recv(size)
        else:
            raise TypeError('Expecting a file descriptor, file, or socket')

    def search(self, pattern, maxread=-1, searchwindowsize=-1, ignorecase=-1):
        """Search for `pattern` in the input.

        The `pattern` parameter must be a string, an exception, or a list of
        strings and exceptions.

        If the pattern is found, the index of the match in the pattern list
        is returned. If pattern was not a list, then 0 is returned as the
        index.

        The parameters `maxread`, `searchwindowsize` and `ignorecase`, if
        provided, override the values given for those paramters in the
        constructor.
        """
        if maxread == -1:
            maxread = self.maxread
        if searchwindowsize == -1:
            searchwindowsize = self.searchwindowsize
        if ignorecase == -1:
            ignorecase = self.ignorecase
        patterns = []
        exception_list = []
        if not isinstance(pattern, list):
            pattern = [pattern]
        for ix,pattern in enumerate(pattern):
            if isinstance(pattern, compat.basestring):
                patterns.append('(?P<pattern_%d>%s)' % (ix, pattern))
            elif issubclass(pattern, Exception):
                exception_list.append((ix, pattern))
            else:
                raise TypeError('Expecting (list of) string or Exception')
        pattern = '|'.join([pattern for pattern in patterns])
        flags = re.DOTALL
        if self.ignorecase:
            flags |= re.IGNORECASE
        regex = re.compile(pattern, flags)
        while True:
            if pattern:
                match = regex.search(self.buffer)
            else:
                match = None
            if match:
                self.before = self.buffer[:match.start()]
                self.after = self.buffer[match.start():match.end()]
                self.match = match
                for key,value in match.groupdict().iteritems():
                    if key.startswith('pattern_') and value:
                        index = int(key[8:])
                        break
                else:
                    raise AssertionError('Got a match but not of the patterns matched??')
                self.match_index = index
                self.buffer = self.buffer[match.end():]
                return self.match_index
            try:
                buf = self.read(maxread)
            except Exception as e:
                exception = e
            else:
                exception = None if buf else EOF('End of file')
            if exception:
                for ix,e in exception_list:
                    if isinstance(exception, e):
                        self.before = self.buffer
                        self.after = ''
                        self.buffer = ''
                        self.match = None
                        self.match_index = ix
                        return ix
                else:
                    raise exception
            self.buffer += buf
            if searchwindowsize is not None and len(buffer) > searchwindowsize:
                self.buffer = self.buffer[-searchwindowsize:]
