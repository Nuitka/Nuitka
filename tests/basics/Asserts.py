# 
#     Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Python test that I originally created or extracted from other peoples
#     work. I put my parts of it in the public domain. It is at least Free
#     Software where it's copied from other people. In these cases, I will
#     indicate it.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the new code, or in the alternative
#     a BSD license to the new code, should your jurisdiction prevent this. This
#     is to reserve my ability to re-license the code at any time.
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
