#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2010-2012 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.


class Spawn(object):
    """Spawn object.
    
    This object is mixed in with Process, Terminal and NBIO to produce
    the pexpect spawn() API.
    """

