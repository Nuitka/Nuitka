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

def tryContinueFinallyTest():
    for x in range(10):
        try:
            if x % 2 == 1:
                continue
        finally:
            yield x

def tryBreakFinallyTest():
    for x in range(10):
        try:
            if x == 5:
                break
        finally:
            yield x

def tryFinallyAfterYield():
    try:
        yield 3
    finally:
        print "Executing finally"


print "Check if finally is executed in a continue using for loop:"
print tuple( tryContinueFinallyTest() )

print "Check if finally is executed in a break using for loop:"
print tuple( tryBreakFinallyTest() )

print "Check what try yield finally something does:"
print tuple( tryFinallyAfterYield() )
