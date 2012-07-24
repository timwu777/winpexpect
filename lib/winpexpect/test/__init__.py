#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import os
import sys
import shutil
import tempfile


def assert_raises(exc, func, *args):
    """Like nose.tools.assert_raises but returns the exception."""
    try:
        func(*args)
    except Exception as e:
        if isinstance(e, exc):
            return e
        raise
    raise AssertionError('%s not raised' % exc.__name__)


class UnitTest(object):
    """Base class for unit tests."""

    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.__tmpdir = cls.tmpdir
        cls.prevdir = os.getcwd()
        os.chdir(cls.tmpdir)
        cls.tmpdirs = []

    @classmethod
    def teardown_class(cls):
        os.chdir(cls.prevdir)
        assert cls.tmpdir == cls.__tmpdir  # just to be sure..
        shutil.rmtree(cls.tmpdir)
        for tmpdir in cls.tmpdirs:
            shutil.rmtree(tmpdir)

    def setup(self):
        self.open_files = []

    def teardown(self):
        for fd in self.open_files:
            fd.close()

    def tempfile(self, contents=None):
        fd, fname = tempfile.mkstemp(dir=self.tmpdir)
        if contents is not None:
            os.write(fd, contents)
        os.close(fd)
        return fname

    def tempdir(self):
        tmpdir = tempfile.mkdtemp()
        self.tmpdirs.append(tmpdir)
        return tmpdir

    def open(self, fname, *args, **kwargs):
        fd = open(fname, *args, **kwargs)
        self.open_files.append(fd)
        return fd


class PosixTest(UnitTest):
    """A test that is only run on Posix systems."""

    @classmethod
    def setup_class(cls):
        try:
            import posix
        except ImportError:
            raise SkipTest('Not running Posix tests on "%s"' % sys.platform)
        super(PosixTest, cls).setup_class()


class WindowsTest(UnitTest):
    """A test that is only run on Windows systems."""

    @classmethod
    def setup_class(cls):
        try:
            import msvcrt
        except ImportError:
            raise SkipTest('Not running Windows tests on "%s"' % sys.platform)
        super(PosixTest, cls).setup_class()
