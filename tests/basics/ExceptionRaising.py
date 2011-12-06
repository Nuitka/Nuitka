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
import sys

def raiseExceptionClass():
    raise ValueError

try:
    raiseExceptionClass()
except Exception, e:
    print e, repr(e), type(e)

def raiseExceptionInstance():
    raise ValueError( "hallo" )

print "*" * 20

try:
    raiseExceptionInstance()
except Exception, f:
    print f, repr(f), type(f)


def raiseExceptionAndReraise():
    try:
        x = 0
        y = x / x
    except:
        raise

print "*" * 20

try:
    raiseExceptionAndReraise()
except:
    print "Catched reraised"

def raiseNonGlobalError():
    return undefined_value

print "*" * 20

try:
   raiseNonGlobalError()
except:
   print "NameError caught"

def raiseIllegalError():
    class X(object):
        pass

    raise X()

print "*" * 20

try:
    raiseIllegalError()
except TypeError, E:
    print "New style class exception correctly rejected:", E
except:
    print sys.exc_info()
    assert False, "Error, new style class exception was not rejected"


def raiseCustomError():
    raise ClassicClassException()

class ClassicClassException:
    pass

print "*" * 20

try:
    raiseCustomError()
except ClassicClassException:
    print "Caught classic class exception"
except:
    print sys.exc_info()
    assert False, "Error, old style class exception was not caught"

def checkTraceback():
    import sys, traceback

    try:
        raise "me"
    except:
        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None

        print "Check traceback:"

        traceback.print_tb( sys.exc_info()[2], file = sys.stdout )

        print "End of traceback"

        print "Type is", sys.exc_info()[0]
        print "Value is", sys.exc_info()[1]

print "*" * 20

checkTraceback()

def checkExceptionConversion():
    try:
        raise Exception( "some string")
    except Exception, err:
        print "Catched raised object", err, type( err )

    try:
        raise Exception, "some string"
    except Exception, err:
        print "Catched raised type, value pair", err, type( err )


print "*" * 20
checkExceptionConversion()

def checkExcInfoScope():
    try:
        raise "me"
    except:
        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None

    assert sys.exc_info()[0] is not None
    assert sys.exc_info()[1] is not None
    assert sys.exc_info()[2] is not None

    print "Exc_info remains visible after exception handler"

    def subFunction():
        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None

    subFunction()

print "*" * 20

sys.exc_clear()

checkExcInfoScope()

# Check that the sys.exc_info is cleared again, after being set inside the
# function checkExcInfoScope, it should now be clear again.
assert sys.exc_info()[0] is None
assert sys.exc_info()[1] is None
assert sys.exc_info()[2] is None

def checkDerivedCatch():
    class A:
        pass
    class B(A):
        pass

    a = A()
    b = B()

    try:
        raise A, b
    except B, v:
        print "Caught B", v
    else:
        print "Not caught A class"

    try:
        raise B, a
    except TypeError, e:
        print "TypeError with pair form for class not taking args:", e


print "*" * 20

checkDerivedCatch()

def checkNonCatch1():
    print "Testing if the else branch is executed in the optimizable case"
    try:
        0
    except TypeError:
        print "Should not catch"
    else:
        print "Executed else branch correctly"


def checkNonCatch2():

    try:
        print "Testing if the else branch is executed in the non-optimizable case"
    except TypeError:
        print "Should not catch"
    else:
        print "Executed else branch correctly"


print "*" * 20
checkNonCatch1()
checkNonCatch2()

print "*" * 20
def checkRaisingRaise():
    print "Checking raise that has exception arg that raises an error itself."

    try:
        raise 1/0

    except Exception, e:
        print "Had exception", e

    try:
        raise TypeError, 1/0

    except Exception, e:
        print "Had exception", e


    try:
        raise TypeError, 7, 1/0

    except Exception, e:
        print "Had exception", e


checkRaisingRaise()

def checkMisRaise():
    raise

try:
    checkMisRaise()
except Exception, e:
    print "Without exception, raise gives:", e
