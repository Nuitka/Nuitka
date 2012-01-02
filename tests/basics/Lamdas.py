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
def lamdaContainer( x ):
    f = lambda c : c
    g = lambda c : c if x else c*c
    # h = lambda c: 'a' <= c <= 'z'

    y = f(x)

    if 'a' <= x <= y <= 'z':
        print "Four"

    if 'a' <= x <= 'z':
        print "Yes"

    if 'a' <= x > 'z':
        print "Yes1"

    if 'a' <= (1 if x else 2 ) > 'z':
        print "Yes2"

    if 'a' <= (1 if x else 2 ) > 'z' > i:
        print "Yes3"

    z = lambda huhu = y : huhu

    print "Lambda defaulted gives", z()

lamdaContainer( "b" )

def lambaGenerator():
    x = lambda : (yield 3)

    gen = x()
    print "Lambda generator gives", gen.next()

lambaGenerator()
