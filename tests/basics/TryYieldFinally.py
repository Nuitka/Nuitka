#
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts and resulting tests are too small to be protected and therefore
#     is in the public domain.
#
#     If you submit Kay Hayen patches to this in either form, you automatically
#     grant him a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. Obviously it
#     won't affect code that comes to him indirectly or code you don't submit to
#     him.
#
#     This is to reserve my ability to re-license the official code at any time,
#     to put it into public domain or under PSF.
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
