#!/usr/bin/env python
#
#     Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are in the public domain. It is at least Free Software
#     where it's copied from other people. In these cases, it will normally be
#     indicated.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     Please leave the whole of this copyright notice intact.
#

# Setup file for pybench
#
# This file has to import all tests to be run; it is executed as
# Python source file, so you can do all kinds of manipulations here
# rather than having to edit the tests themselves.
#
# Note: Please keep this module compatible to Python 1.5.2.
#
# Tests may include features in later Python versions, but these
# should then be embedded in try-except clauses in this configuration
# module.

# Defaults
Number_of_rounds = 10
Warp_factor = 10

# Import tests
from Arithmetic import *
from Calls import *
from Constructs import *
from Lookups import *
from Instances import *
try:
    from NewInstances import *
except ImportError:
    pass
from Lists import *
from Tuples import *
from Dict import *
from Exceptions import *
try:
    from With import *
except SyntaxError:
    pass
from Imports import *
from Strings import *
from Numbers import *
try:
    from Unicode import *
except (ImportError, SyntaxError):
    pass
