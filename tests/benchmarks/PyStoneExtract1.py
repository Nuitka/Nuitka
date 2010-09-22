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
# This taken from CPython's pystone test, and is an extract of it I made
# to analyse the differences between CPython and Nuitka performance. It
# was under PSF 2 license. It's not very useful anymore, but it is under
# that license still.

from time import clock

LOOPS = 5000000
__version__ = "1.1"


Char1Glob = '\0'
Char2Glob = '\0'

BoolGlob = 0

def Proc4():
    global Char2Glob

    BoolLoc = Char1Glob == 'A'
    BoolLoc = BoolLoc or BoolGlob
    Char2Glob = 'B'

def benchmark( loops ):
    for i in xrange( loops ):
        Proc4()


if __name__ == "__main__":
    benchmark( LOOPS )
