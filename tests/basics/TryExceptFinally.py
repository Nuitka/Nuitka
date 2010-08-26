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
