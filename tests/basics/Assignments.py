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
def someFunction():
    a = 2
    print "Simple assignment to variable:", a

    b = c = 3
    print "Assignment to 2 variables", b, c

    z = [ 1, 2, 3 ]
    z[2] = z[1] = 5

    print "Assignment to list subscripts:", z

    d, e = 1, 2
    print "Assignment to variable tuple:", d, e

    [ f, g ] = 7, 9
    print "Assignment to variable list:", f, g

    j = [ h, i ] = ( 7, 9 )
    print "Complex Assignment from variabe list:", j, type(j), h, i

    a, (b,c) = 1, (2,3 )
    print "Assigment to nested tuples:", a, b, c

    v = [ 1, 2, 3, 4 ]
    v[2:3] = (8,9)
    print "Assignment to list slice", v


def varargsFunction( *args ):
    f1, f2, f3, f4 = args

    print "Assignment from list", f1, f2, f3, f4


def otherFunction():
    class Iterable:
        def __iter__( self ):
            return iter(range(3))

    a, b, c = Iterable()

    print "Assignments from iterable", a ,b ,c

    print "Assignments from too small iterable",

    try:
        f, g = 1,
    except Exception, e:
        print "gave", type(e), e

        try:
            print f
        except UnboundLocalError:
            print "Variable f is untouched"

        try:
            print g
        except UnboundLocalError:
            print "Variable g is untouched"

    print "Assignments from too large iterable",

    try:
        d, j = 1, 2, 3
    except Exception, e:
        print "gave", type(e), e

        try:
            print d
        except UnboundLocalError:
            print "Variable d is untouched"

        try:
            print j
        except UnboundLocalError:
            print "Variable j is untouched"



def anotherFunction():
    d = {}

    print "Assignment to dictionary with comma subscript:",
    # d[ "f" ] = 3

    d[ "a", "b" ] = 6
    d[ "c", "b" ] = 9

    print sorted( d.iteritems() )


def swapVariables():
    print "Strange swap form:"
    a = 1
    b = 2

    a, b, a = b, a, b

    print a, b

def interuptedUnpack():
    a = 1
    b = 2

    try:
        c, d = a,
    except ValueError, e:
        print "ValueError", e

        try:
            print c
        except UnboundLocalError, e:
            print "UnboundLocalError", e

someFunction()
varargsFunction(1,2,3,4)
otherFunction()
anotherFunction()
swapVariables()
interuptedUnpack()
