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
        print type(e), e

    print "Assignments from too large iterable",

    try:
        d, e = 1, 2, 3
    except Exception, e:
        print type(e), e


def anotherFunction():
    d = {}

    print "Assignment to dictionary with comma subscript:",

    d[ "a", "b" ] = 6
    d[ "c", "b" ] = 9

    print sorted( d.iteritems() )


someFunction()
varargsFunction(1,2,3,4)
otherFunction()
anotherFunction()
