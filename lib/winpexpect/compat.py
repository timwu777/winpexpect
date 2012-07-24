#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import sys

if sys.version_info[0] == 3:
    unicode = str
    basestring = str
    buffer = memoryview
else:
    unicode = unicode
    basestring = basestring
    buffer = buffer
