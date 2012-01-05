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
"Some doc"

def tryScope1(x):
    try:
        try:
            x += 1
        finally:
            print "Finally is executed"

            try:
                z = 1
            finally:
                print "Deep Nested finally is executed"
    except:
        print "Exception occured"
    else:
        print "No exception occured"

tryScope1( 1 )
print "*" * 20
tryScope1( [ 1 ] )

def tryScope2( x, someExceptionClass ):
    try:
        x += 1
    except someExceptionClass, e:
        print "Exception class from argument occured:", someExceptionClass, e
    else:
        print "No exception occured"

def tryScope3( x ):
    if x:
        try:
            x += 1
        except TypeError:
            print "TypeError occured"
    else:
        print "Not taken"


print "*" * 20

tryScope2( 1, TypeError )
tryScope2( [ 1 ], TypeError )

print "*" * 20

tryScope3( 1 )
tryScope3( [ 1 ] )
tryScope3( [] )

print "*" * 20

def tryScope4( x ):
    try:
        x += 1
    except:
        print "exception occured"
    else:
        print "no exception occured"
    finally:
        print "finally obeyed"

tryScope4( 1 )
tryScope4( [ 1 ] )
