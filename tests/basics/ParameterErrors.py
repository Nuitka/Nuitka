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

def functionNoParameters():
    pass

print "Call a function with no parameters with a plain argument:"

try:
    functionNoParameters( 1 )
except TypeError, e:
    print e

print "Call a function with no parameters with a keyword argument:"

try:
    functionNoParameters( z = 1 )
except TypeError, e:
    print e

def functionOneParameter( a ):
    print a
    pass

print "Call a function with one parameter with two plain arguments:"

try:
    functionOneParameter( 1, 1 )
except TypeError, e:
    print e

print "Call a function with two parameters with three plain arguments:"

def functionTwoParameters( a, b ):
    pass

try:
    functionTwoParameters( 1, 2, 3 )
except TypeError, e:
    print e

print "Call a function with two parameters with one plain argument:"

try:
    functionTwoParameters( 1 )
except TypeError, e:
    print e

print "Call a function with two parameters with one keyword argument:"

try:
    functionTwoParameters( a = 1 )
except TypeError, e:
    print e

print "Call a function with two parameters with three keyword arguments:"

try:
    functionTwoParameters( a = 1, b = 2, c = 3 )
except TypeError, e:
    print e
