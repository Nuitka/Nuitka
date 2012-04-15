#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
import sys

def raiseExceptionClass():
    raise ValueError

try:
    raiseExceptionClass()
except Exception, e:
    print "Caught exception", e, repr(e), type(e)

def raiseExceptionInstance():
    raise ValueError( "hallo" )

print "*" * 20

try:
    raiseExceptionInstance()
except Exception, f:
    print f, repr(f), type(f)

print sys.exc_info()

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


class ClassicClassException:
    pass

def raiseCustomError():
    raise ClassicClassException()

print "*" * 20

try:
    try:
        raiseCustomError()
    except ClassicClassException:
        print "Caught classic class exception"
    except:
        print sys.exc_info()
        assert False, "Error, old style class exception was not caught"
except TypeError, e:
    print "Python3 hates to even try and catch classic classes", e
else:
    print "Classic exception catching was considered fine."

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

    if sys.version_info[0] < 3:
        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None

    print "Exc_info remains visible after exception handler"


    def subFunction():
        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None

    try:
        raise "me"
    except:
        assert sys.exc_info()[0] is not None
        assert sys.exc_info()[1] is not None
        assert sys.exc_info()[2] is not None

        subFunction()




print "*" * 20

if sys.version_info[0] < 3:
    sys.exc_clear()

checkExcInfoScope()

# Check that the sys.exc_info is cleared again, after being set inside the
# function checkExcInfoScope, it should now be clear again.
assert sys.exc_info()[0] is None
assert sys.exc_info()[1] is None
assert sys.exc_info()[2] is None

def checkDerivedCatch():
    class A( BaseException ):
        pass
    class B( A ):
        def __init__( self ):
            pass

    a = A()
    b = B()

    try:
        raise A, b
    except B, v:
        print "Caught B", v
    except A, v:
        print "Didn't catch as B, but as A, Python3 does that", v
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


def nestedExceptions( a, b ):
    try:
        a / b
    except ZeroDivisionError:
        a / b

try:
    nestedExceptions( 1, 0 )
except Exception, e:
    print "Nested exception gives", e

def unpackingCatcher():
    try:
        raise ValueError(1,2)
    except ValueError as (a,b):
        print "Unpacking caught exception and unpacked", a, b

unpackingCatcher()
