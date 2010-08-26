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



def simple_comparisons( x, y ):
    if 'a' <= x <= y <= 'z':
        print "One"

    if 'a' <= x <= 'z':
        print "Two"

    if 'a' <= x > 'z':
        print "Three"

print "Simple comparisons:"

simple_comparisons( "c", "d" )

def side_effect():
    print "<side_effect>"

    return 7

def side_effect_comparisons():
    print "Should have side effect:"

    print 1 < side_effect() < 9

    print "Should not have side effect due to short circuit"

    print 3 < 2 < side_effect() < 9

print "Check for expected side effects only:"

side_effect_comparisons()

def function_torture_is():
    a = ( 1, 2, 3 )

    for x in a:
        for y in a:
            for z in a:
                print x, y, z, ":", x is y is z

function_torture_is()
