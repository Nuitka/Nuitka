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
        print b

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
