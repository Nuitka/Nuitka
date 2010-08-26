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
# -*- coding: utf-8 -*-

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


lamdaContainer( "b" )


