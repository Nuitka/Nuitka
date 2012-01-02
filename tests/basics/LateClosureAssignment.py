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

def closureTest1():
    # Assign, but the value is not supposed to be used by the function, instead the later
    # update is effective.
    d = 1

    def subby():
        return d

    d = 22222*2222

    return subby()


def closureTest2():
    # Using a closure variable that is not initialized at the time it is closured should
    # work as well.

    def subby():
        return d

    d = 2222*2222

    return subby()

def closureTest3():
    def subby():
        return d

    try:
        return subby()
    except NameError:
        return 88

d = 1

def scopeTest4():
    try:
        return d

        d = 1
    except UnboundLocalError, e:
        return e


print "Test closure where value is overwritten:", closureTest1()
print "Test closure where value is assigned only late:", closureTest2()

print "Test function where closured value is never assigned:", closureTest3()

print "Scope test where UnboundLocalError is expected:", scopeTest4()


def function():
    pass

class ClosureLocalizerClass:
    print "Function before assigned in a class", function

    function = 1

    print "Function after it was assigned in class", function

ClosureLocalizerClass()

def ClosureLocalizerFunction():
    try:
        function = function

        print "Function didn't give unbound local error"
    except UnboundLocalError:
        print "Function gave unbound local error when accessing function before assignment."

ClosureLocalizerFunction()

class X:
    def __init__( self, x ):
        self.x = x

def changingClosure():
    a = 1

    def closureTaker():
        return X(a)

    x = closureTaker()
    a=2
    print x.x
    x = closureTaker()
    print x.x

changingClosure()
