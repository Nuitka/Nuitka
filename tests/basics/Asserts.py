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


def testAssert1():
    assert False

    return 1

def testAssert2():
    assert True

    return 1

def testAssert3():
    assert False, "argument"

    return 1

try:
    print "Function that will assert."
    testAssert1()
    print "No exception."
except Exception, e:
    print "Raised", type(e), e

try:
    print "Function that will not assert."
    testAssert2()
    print "No exception."
except Exception, e:
    print "Raised", type(e), e

try:
    print "Function that will assert with argument."
    testAssert3()
    print "No exception."
except Exception, e:
    print "Raised", type(e), e
