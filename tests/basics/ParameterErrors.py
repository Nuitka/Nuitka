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

print "Call a function with one parameter with two plain arguments:"

try:
    functionOneParameter( 1, 1 )
except TypeError, e:
    print e

print "Call a function with two parameters with three plain arguments:"

def functionTwoParameters( a, b ):
    print a, b

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

class MethodContainer:
    def methodNoParameters( self ):
        pass

    def methodOneParameter( self, a ):
        print a

    def methodTwoParameters( self, a, b ):
        print a, b

obj = MethodContainer()

print "Call a method with no parameters with a plain argument:"

try:
    obj.methodNoParameters( 1 )
except TypeError, e:
    print e

print "Call a method with no parameters with a keyword argument:"

try:
    obj.methodNoParameters( z = 1 )
except TypeError, e:
    print e

print "Call a method with one parameter with two plain arguments:"

try:
    obj.methodOneParameter( 1, 1 )
except TypeError, e:
    print e

print "Call a method with two parameters with three plain arguments:"

try:
    obj.methodTwoParameters( 1, 2, 3 )
except TypeError, e:
    print e

print "Call a method with two parameters with one plain argument:"

try:
    obj.methodTwoParameters( 1 )
except TypeError, e:
    print e

print "Call a method with two parameters with one keyword argument:"

try:
    obj.methodTwoParameters( a = 1 )
except TypeError, e:
    print e

print "Call a method with two parameters with three keyword arguments:"

try:
    obj.methodTwoParameters( a = 1, b = 2, c = 3 )
except TypeError, e:
    print e

def functionPosBothStarArgs( a, b, c, *l, **d ):
    print a, b, c, l, d

l = [2]
d = { "other" : 7 }

print "Call a function with both star arguments and too little arguments:"

try:
    functionPosBothStarArgs( 1,  *l, **d )
except TypeError, e:
    print e
