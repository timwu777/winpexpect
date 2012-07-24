#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import os
from textwrap import dedent

from winpexpect import *
from winpexpect.test import *
from winpexpect.exception import *


class TestSearch(UnitTest):

    def test_search(self):
        fname = self.tempfile(dedent("""\
                line1
                line2
                line3
                """))
        fin = self.open(fname)
        searcher = Searcher(fin)
        ix = searcher.search('line2')
        assert ix == 0
        assert searcher.before == 'line1\n'
        assert searcher.after == 'line2'
        assert hasattr(searcher.match, 'groups')
        assert searcher.match_index == 0

    def test_search_list(self):
        fname = self.tempfile(dedent("""\
                line1
                line2
                line3
                """))
        fin = self.open(fname)
        searcher = Searcher(fin)
        ix = searcher.search(['line1', 'line3'])
        assert ix == 0
        assert searcher.before == ''
        assert searcher.after == 'line1'
        assert hasattr(searcher.match, 'groups')
        assert searcher.match_index == 0
        ix = searcher.search(['line1', 'line3'])
        assert ix == 1
        assert searcher.before == '\nline2\n'
        assert searcher.after == 'line3'
        assert hasattr(searcher.match, 'groups')
        assert searcher.match_index == 1

    def test_eof(self):
        fname = self.tempfile('line1\n')
        fin = self.open(fname)
        searcher = Searcher(fin)
        ix = searcher.search(['line2', EOF])
        assert ix == 1
        assert searcher.before == 'line1\n'
        assert searcher.after == ''
        assert searcher.match is None
        assert searcher.match_index == 1
        fin.seek(0)
        searcher = Searcher(fin)
        ix = searcher.search(EOF)
        assert ix == 0
        assert searcher.before == 'line1\n'
        assert searcher.after == ''
        assert searcher.match is None
        assert searcher.match_index == 0
        fin.seek(0)
        searcher = Searcher(fin)
        assert_raises(EOF, searcher.search, 'line2')
        fin.seek(0)
        searcher = Searcher(fin)
        assert_raises(EOF, searcher.search, [])

    def test_fd_input(self):
        fname = self.tempfile('line1\n')
        fd = os.open(fname, os.O_RDONLY)
        searcher = Searcher(fd)
        ix = searcher.search('line1')
        assert ix == 0
        assert searcher.before == ''
        assert searcher.after == 'line1'
        assert hasattr(searcher.match, 'groups')
        assert searcher.match_index == 0
