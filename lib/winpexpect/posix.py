#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import os
import os.path
import pty
import time
import stat
import fcntl
import errno
import select
import signal
import termios
import struct
import itertools

from collections import namedtuple

from winpexpect import compat
from winpexpect.exception import TIMEOUT
from winpexpect.process import Process
from winpexpect.terminal import Terminal
from winpexpect.nbio import NBIO


def split_command_line(cmdline):
    """Split a commandline into a list of words. This supports bourne shell
    style escaping with double quotes, single quotes, and backslashes.
    """
    (s_free, s_in_escape, s_in_single_quote,
            s_in_double_quote, s_in_escape_in_double_quote) = range(5)
    state = namedtuple('state', ('state', 'word'))
    state.state = s_free
    state.word = []
    result = []
    for ch in itertools.chain(cmdline, ['EOI']):
        if state.state == s_free:
            if ch == "\\":
                state.state = s_in_escape
            elif ch == "'":
                state.state = s_in_single_quote
            elif ch == '"':
                state.state = s_in_double_quote
            elif ch in (' ', '\t', 'EOI'):
                if state.word:
                    result.append(''.join(state.word))
                    del state.word[:]
            elif ch == '\n':
                raise ValueError('You cannot enter multiple commands')
            else:
                state.word.append(ch)
        elif state.state == s_in_escape:
            if ch != 'EOI':
                state.state = s_free
            if ch != '\n':
                state.word.append(ch)
        elif state.state == s_in_single_quote:
            if ch == "'":
                state.state = s_free
            else:
                state.word.append(ch)
        elif state.state == s_in_double_quote:
            if ch == '"':
                state.state = s_free
            elif ch == '\\':
                state.state = s_in_escape_in_double_quote
            else:
                state.word.append(ch)
        elif state.state == s_in_escape_in_double_quote:
            state.state = s_in_double_quote
            if ch not in '\\"\n':
                state.word.append('\\')
            if ch != '\n':
                state.word.append(ch)
    if state.state != s_free:
        raise ValueError('Illegal quoting in command line')
    return result


def which(command):
    """Find the executale `command` in $PATH."""
    if command.startswith('/'):
        return command if os.access(command, os.X_OK) else None
    elif command.startswith('.'):
        command = os.path.abspath(command)
        return command if os.access(command, os.X_OK) else None
    path = os.environ.get('PATH')
    path = path.split(os.pathsep)
    for base in path:
        fname = os.path.join(base, command)
        if os.access(fname, os.X_OK):
            return fname


def closefrom(fd):
    """Close add file descriptors starting at `fdlow'."""
    def _close(fd):
        """Close a file descriptor ignoring errors."""
        try:
            os.close(fd)
        except OSError:
            pass
    # Try a Linux optimization first
    try:
        st = os.stat('/proc/self/fd')
    except OSError:
        st = None
    if st and stat.S_ISDIR(st.st_mode):
        fds = map(int, os.listdir('/proc/self/fd'))
        for fd1 in fds:
            if fd1 >= fd:
                _close(fd1)
        return
    # This should work on most Unixes
    maxfd = os.sysconf("SC_OPEN_MAX")
    for fd1 in range(fd, maxfd):
        _close(fd1)


class PosixProcess(Process):
    """POSIX version of Process."""

    def __init__(self, command, args=None, cwd=None, env=None, closefds=None):
        """Constructor."""
        self._parse_args(command, args)
        self.cwd = cwd
        self.env = env
        self.closefds = closefds
        self.pid = None
        self.ptyfd = None
        self.encoding = None
        self.exitstatus = None
        self.termsig = None

    def _parse_args(self, command, args):
        """Parse the command line and arguments."""
        if args:
            args.insert(0, command)
        else:
            args = split_command_line(command)
            command = args[0]
        self.command = command
        self.args = args

    def _get_encoding(self, env):
        """Try to determine the encoding."""
        try:
            locale, encoding = env['LANG'].split('.')
        except (KeyError, ValueError):
            return None
        return encoding.lower()

    def start(self):
        """Start the child."""
        if self.pid is not None:
            return
        path = which(self.command)
        if path is None:
            raise ProcessError('Could not find %s in $PATH' % command)
        env = self.env
        if env is None:
            env = os.environ
        encoding = self._get_encoding(env)
        pid, master = os.forkpty()
        if pid == 0:
            if self.closefds:
                closefrom(3)
            if self.cwd:
                os.chdir(self.cwd)
            os.execve(path, self.args, env)
        self.pid = pid
        self.ptyfd = master
        self.encoding = encoding
        self.termsig = None
        self.exitstatus = None

    def fileno(self):
        if self.ptyfd is None:
            raise RuntimeError('You need to call start() first')
        return self.ptyfd

    def read(self, size):
        if self.ptyfd is None:
            raise RuntimeError('You need to call start() first')
        buf = os.read(self.ptyfd, size)
        if self.encoding:
            buf = buf.decode(self.encoding)
        return buf

    def write(self, buf):
        if self.ptyfd is None:
            raise RuntimeError('You need to call start() first.')
        if isinstance(buf, compat.unicode):
            buf = buf.encode(self.encoding)
        nbytes = os.write(self.ptyfd, buf)
        return nbytes

    def close(self):
        if self.ptyfd is None:
            return
        try:
            os.close(self.ptyfd)
        except OSError:
            pass
        self.ptyfd = None

    def wait(self, timeout=None):
        """Wait until the process exits.
        
        Note that unread data on the pty will prevent the child from exiting.
        So you either need to read all data, or close() the process first.
        """
        if self.pid is None:
            raise RuntimeError('You need to call start() first.')
        if timeout is not None:
            endtime = time.time() + timeout
            flags = os.WNOHANG
        else:
            flags = 0
        while True:
            try:
                pid, status = os.waitpid(self.pid, flags)
            except OSError as e:
                if e.errno == errno.EINTR:
                    continue
                elif e.errno == errno.ECHILD:
                    # Someone else reaped our child..
                    pid, status = (self.pid, None)
                    break
                else:
                    raise
            if pid > 0:
                break
            assert timeout is not None
            timeleft = endtime - time.time()
            if timeleft <= 0:
                break
            # Sleep anywhere between 0.1 and 1 second depending on the timeout.
            # This is not ideal because we may know that a child has exited
            # only 1 seconds after it has happened. The alternative is
            # installing a signal handler via SIGCHLD which is even less ideal
            # because it affects how this module can be used together with
            # other libraries that also need to capture SIGCHLD.
            time.sleep(max(0.1, min(1, timeout/10.0)))
        if self.pid == 0:
            return False
        assert pid == self.pid
        self.pid = None
        if status is not None:
            self.termsig = os.WTERMSIG(status) if os.WIFSIGNALED(status) else None
            self.exitstatus = os.WEXITSTATUS(status) if os.WIFEXITED(status) else None
        self.close()
        return status is not None

    def isalive(self):
        """Return whether or not the process is alive."""
        if self.pid is None:
            return False
        while True:
            try:
                pid, status = os.waitpid(self.pid, os.WNOHANG)
            except OSError as e:
                if e.errno == errno.EINTR:
                    continue
                elif e.errno == errno.ECHILD:
                    pid, status = (self.pid, None)
                    break
                else:
                    raise
            break
        if pid == 0:
            return True
        assert pid == self.pid
        self.pid = None
        if status is not None:
            self.termsig = os.WTERMSIG(status) if os.WIFSIGNALED(status) else None
            self.exitstatus = os.WEXITSTATUS(status) if os.WIFEXITED(status) else None
        self.close()
        return False

    def kill(self, signal):
        """Send a signal to the child process."""
        if self.pid is None:
            raise RuntimeError('You need to call start() first')
        os.kill(self.pid, signal)

    def terminate(self, timeout=None):
        """Terminate the process."""
        if self.pid is None:
            return
        if timeout is not None:
            timeout /= 2.0
        self.kill(signal.SIGTERM)
        self.wait(timeout)
        if not self.isalive():
            return True
        self.kill(signal.SIGKILL)
        self.wait(timeout)
        return not self.isalive()


class PosixTerminal(Terminal):
    """A terminal for Posix style systems."""

    def __init__(self, fd):
        self.ttyfd = fd

    def getecho(self):
        """Return the echo mode."""
        attrs = termios.tcgetattr(self.ttyfd)
        return bool(attrs[3] & termios.ECHO)

    def setecho(self, echo):
        """Set the echo mode."""
        attrs = termios.tcgetattr(self.ttyfd)
        if echo:
            attrs[3] |= termios.ECHO
        else:
            attrs[3] &= ~termios.ECHO
        termios.tcsetattr(self.ttyfd, termios.TCSANOW, attrs)

    def getwinsize(self):
        """Return the window size as a (rows, cols) tuple."""
        packed = fcntl.ioctl(self.ttyfd, termios.TIOCGWINSZ, 'xxxx')
        rows, cols = struct.unpack('@HH', packed)
        return (rows, cols)

    def setwinsize(self, rows, cols):
        """Set the window size."""
        packed = fcntl.ioctl(self.ttyfd, termios.TIOCGWINSZ, 'xxxxxxxx')
        crows, ccols, xpix, ypix = struct.unpack('@HHHH', packed)
        packed = struct.pack('@HHHH', rows, cols, xpix, ypix)
        fcntl.ioctl(self.ttyfd, termios.TIOCSWINSZ, packed)

    def cchar(self, name):
        """Return a special control character."""
        index = getattr(termios, name, None)
        if index is None:
            raise ValueError('No such control character: %s' % name)
        attr = termios.tcgetattr(self.ttyfd)
        cc = attr[6][index]
        return cc


class PosixNBIO(NBIO):
    """Posix Non-Blocking I/O.

    If a timeout is set to something else that None, the file descriptor will
    be put in non-blocking mode. Timeouts > 0 are are implemented with select().
    """

    def __init__(self, fd, timeout=None):
        self.fd = fd
        self.settimeout(timeout)

    def settimeout(self, timeout):
        self.timeout = timeout
        flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        if self.timeout is None:
            flags = flags & ~os.O_NONBLOCK
        else:
            flags = flags | os.O_NONBLOCK
        fcntl.fcntl(self.fd, fcntl.F_SETFL, flags)

    def read(self, nbytes):
        if self.timeout is not None:
            endtime = time.time() + self.timeout
        while True:
            try:
                buf = os.read(self.fd, nbytes)
            except OSError as e:
                if e.errno == errno.EINTR:
                    continue
                elif e.errno == errno.EAGAIN:
                    buf = None
                else:
                    raise
            if self.timeout is None or buf:
                break
            timeleft = endtime - time.time()
            if timeleft < 0:
                raise TIMEOUT('Timeout reading from fd')
            try:
                select.select([self.fd], [], [], timeleft)
            except select.error as e:
                if e[0] != errno.EINTR:
                    raise
        return buf

    def write(self, buf):
        if not isinstance(buf, bytes):
            raise TypeError('Expecting raw bytes not unicode')
        if self.timeout is not None:
            endtime = time.time() + self.timeout
        byteswritten = 0
        buf = compat.buffer(buf)
        while True:
            try:
                nbytes = os.write(self.fd, buf[byteswritten:])
                assert nbytes != 0
                byteswritten += nbytes
            except OSError as e:
                if e.errno == errno.EINTR:
                    continue
                elif e.errno != errno.EAGAIN:
                    raise
            if byteswritten == len(buf):
                break
            if self.timeout is None:
                timeleft = None
            else:
                timeleft = endtime - time.time()
                if timeleft < 0:
                    raise TIMEOUT('Timeout writing to fd')
            try:
                select.select([], [self.fd], [], timeleft)
            except select.error as e:
                if e[0] != errno.EINTR:
                    raise
        return byteswritten
