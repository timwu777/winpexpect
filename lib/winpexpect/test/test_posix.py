#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import sys
import time
import signal
import select
import threading
from nose import SkipTest

from winpexpect.posix import *
from winpexpect.test import *


class TestPosixProcess(PosixTest):

    def test_split_command_line(self):
        split = split_command_line
        assert split('foo') == ['foo']
        assert split('foo bar') == ['foo', 'bar']
        assert split('  foo   bar  ') == ['foo', 'bar']
        assert split('  foo\t bar\t') == ['foo', 'bar']
        assert split('foo bar\\baz') == ['foo', 'barbaz']
        assert split('foo bar\\\nbaz') == ['foo', 'barbaz']
        assert split('foo bar\\"baz\\"') == ['foo', 'bar"baz"']
        assert split("foo 'bar'") == ['foo', 'bar']
        assert split("foo 'bar\\'") == ['foo', 'bar\\']
        assert split('foo "bar"') == ['foo', 'bar']
        assert split('foo"bar"') == ['foobar']
        assert split("foo'bar'") == ["foobar"]
        assert split('foo "bar\\"baz"') == ['foo', 'bar"baz']
        assert split('foo "bar\\\nbaz"') == ['foo', 'barbaz']
        assert split('foo "bar\\\\baz"') == ['foo', 'bar\\baz']
        assert split('foo "bar\\baz"') == ['foo', 'bar\\baz']
        assert_raises(ValueError, split, 'foo bar\\')
        assert_raises(ValueError, split, "foo bar'")
        assert_raises(ValueError, split, 'foo bar"')
        assert_raises(ValueError, split, 'foo bar\nbaz')

    def test_which(self):
        os.mkdir('bin')
        self.open('bin/foo', 'w')
        os.chmod('bin/foo', 0755)
        assert which('bin/foo') is None
        assert which('./bin/foo') == os.path.abspath('./bin/foo')
        assert which('bin/bar') is None
        assert which('./bin/bar') is None
        assert which('/bin/sh') == '/bin/sh'

    def test_process(self):
        cat = PosixProcess('/bin/cat')
        cat.start()
        assert cat.isalive()
        assert isinstance(cat.pid, int)
        assert cat.pid > 0
        assert cat.exitstatus is None
        assert cat.termsig is None
        cat.write('foo\n')
        line = cat.read(10)
        assert line == 'foo\r\n'
        assert cat.terminate(1.0)
        assert not cat.isalive()
        assert cat.exitstatus is None
        assert cat.termsig == signal.SIGTERM

    def test_hangup(self):
        cat = PosixProcess('/bin/cat')
        cat.start()
        cat.close()
        assert cat.wait(1.0)
        assert not cat.isalive()
        assert cat.exitstatus is None
        assert cat.termsig == signal.SIGHUP

    def test_reaped_by_other(self):
        cat = PosixProcess('/bin/cat')
        cat.start()
        assert cat.isalive()
        cat.kill(signal.SIGTERM)
        time.sleep(1.0)
        pid, status = os.waitpid(cat.pid, os.WNOHANG)
        assert pid == cat.pid
        assert not cat.wait(0.0)
        assert cat.exitstatus is None
        assert cat.termsig is None


class TestPosixTerminal(PosixTest):

    def test_echo(self):
        cat = PosixProcess('/bin/cat')
        cat.start()
        terminal = PosixTerminal(cat.fileno())
        assert terminal.getecho() == True
        cat.write('foo\n')
        time.sleep(1)
        line = cat.read(20)
        assert line == 'foo\r\nfoo\r\n'
        cat.terminate()

    def test_noecho(self):
        cat = PosixProcess('/bin/cat')
        cat.start()
        terminal = PosixTerminal(cat.fileno())
        terminal.setecho(False)
        assert terminal.getecho() == False
        cat.write('bar\n')
        time.sleep(1)
        line = cat.read(20)
        assert line == 'bar\r\n'
        terminal.setecho(True)
        assert terminal.getecho() == True
        cat.write('baz\n')
        time.sleep(1)
        line = cat.read(20)
        assert line == 'baz\r\nbaz\r\n'
        cat.terminate()

    def test_eof(self):
        cat = PosixProcess('/bin/cat')
        cat.start()
        terminal = PosixTerminal(cat.fileno())
        cat.write(terminal.cchar('VEOF'))
        time.sleep(1)
        assert not cat.isalive()
        assert cat.exitstatus == 0
        assert cat.termsig is None


class TestPosixNBIO(UnitTest):

    def test_read(self):
        r, w = os.pipe()
        io = PosixNBIO(r)
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
        io = PosixNBIO(w)
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
        rio = PosixNBIO(r)
        wio = PosixNBIO(w)
        wio.settimeout(2)
        bytesread = [0]  # workaround for lack of "nonlocal" in 2.x
        def consume():
            time.sleep(1)
            while True:
                bytesread[0] += len(rio.read(select.PIPE_BUF))
                if bytesread[0] == nbytes:
                    break
        consumer = threading.Thread(target=consume)
        consumer.start()
        byteswritten = wio.write(buf)
        consumer.join()
        assert bytesread[0] == nbytes
        assert byteswritten == nbytes
